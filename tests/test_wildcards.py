from __future__ import annotations

import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import nodes as nodes_module
from nodes import (
    EasyUseAnimaPromptStudioAdvanced,
    EasyUseAnimaPromptStudioAdvancedV2,
    EasyUseAnimaPromptStudioRegional,
    EasyUseAnimaWildcard,
)
from settings import public_settings
import wildcard_engine
from wildcard_engine import (
    DEFAULT_TEST_WILDCARD_FILE,
    WildcardExpansionBudget,
    WildcardExpansionResult,
    ensure_default_wildcard_root,
    expand_wildcard_texts,
    expand_wildcards,
    list_wildcards,
)


class WildcardEngineTests(unittest.TestCase):
    def test_default_root_is_created_with_test_wildcard(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(wildcard_engine, "USER_DATA_DIR", Path(temp)):
                root = ensure_default_wildcard_root()

                self.assertTrue(root.is_dir())
                self.assertEqual(root, Path(temp) / "wildcards")
                self.assertTrue((root / DEFAULT_TEST_WILDCARD_FILE).is_file())

    def test_extra_paths_are_parsed_one_path_per_line(self):
        self.assertEqual(
            wildcard_engine.parse_wildcard_extra_paths('D:/wildcards;E:/ignored\n"custom/wildcards"'),
            ["D:/wildcards;E:/ignored", "custom/wildcards"],
        )

    def test_dynamic_prompt_weight_prefixes_are_stripped(self):
        result = expand_wildcards("{0::a|1::b}", seed=0)

        self.assertEqual(result.text, "b")
        self.assertNotIn("::", result.text)

    def test_extra_roots_override_default_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            extra = root / "extra"
            default = root / "default"
            extra.mkdir()
            default.mkdir()
            (extra / "style.txt").write_text("extra style\n", encoding="utf-8")
            (default / "style.txt").write_text("default style\n", encoding="utf-8")

            result = expand_wildcards("__style__", seed=0, roots=[extra, default])

        self.assertEqual(result.text, "extra style")
        self.assertEqual(result.used_keys, ("style",))

    def test_sequential_mode_uses_seed_modulo_option_count(self):
        self.assertIsNone(wildcard_engine._Selector(4, sequential=True).rng)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "color.txt").write_text("red\nblue\ngreen\n", encoding="utf-8")
            (root / "hair.txt").write_text("short hair\nlong hair\n", encoding="utf-8")

            result = expand_wildcards(
                "__color__, __hair__",
                seed=4,
                mode="순차",
                roots=[root],
            )

        self.assertEqual(result.text, "blue, short hair")

    def test_bare_wildcard_falls_back_to_nested_file_name(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nested = root / "character"
            nested.mkdir()
            (nested / "hair.txt").write_text("black hair\n", encoding="utf-8")

            result = expand_wildcards("__hair__", seed=0, roots=[root])

        self.assertEqual(result.text, "black hair")

    def test_multiselect_can_expand_wildcard_options(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "color.txt").write_text("red\nblue\ngreen\n", encoding="utf-8")

            result = expand_wildcards("{2$$__color__}", seed=0, roots=[root])

        values = [part.strip() for part in result.text.split(",")]
        self.assertEqual(len(values), 2)
        self.assertEqual(len(set(values)), 2)

    def test_direct_self_reference_stops_with_unresolved_token(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.txt").write_text("__a__\n", encoding="utf-8")

            first = expand_wildcards("__a__", seed=0, roots=[root])
            second = expand_wildcards("__a__", seed=0, roots=[root])

        self.assertEqual(first, second)
        self.assertEqual(first.text, "__a__")
        self.assertEqual(first.limit_reason, "cycle")
        self.assertEqual(first.replacement_count, 0)

    def test_proliferating_self_reference_is_blocked_before_growth(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.txt").write_text("__a____a__\n", encoding="utf-8")

            result = expand_wildcards("__a__", seed=0, roots=[root])

        self.assertEqual(result.text, "__a__")
        self.assertEqual(result.limit_reason, "cycle")
        self.assertEqual(result.replacement_count, 0)

    def test_cycle_only_blocks_its_own_branch_in_either_input_order(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.txt").write_text("__a__\n", encoding="utf-8")
            (root / "b.txt").write_text("done\n", encoding="utf-8")

            cycle_first = expand_wildcards("__a__ __b__", seed=0, roots=[root])
            cycle_last = expand_wildcards("__b__ __a__", seed=0, roots=[root])

        self.assertEqual(cycle_first.text, "__a__ done")
        self.assertEqual(cycle_last.text, "done __a__")
        for result in (cycle_first, cycle_last):
            self.assertEqual(result.limit_reason, "cycle")
            self.assertEqual(result.replacement_count, 1)

    def test_cycle_does_not_stop_an_independent_later_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.txt").write_text("__a__\n", encoding="utf-8")
            (root / "b.txt").write_text("__c__\n", encoding="utf-8")
            (root / "c.txt").write_text("done\n", encoding="utf-8")

            result = expand_wildcards("__a__ __b__", seed=0, roots=[root])

        self.assertEqual(result.text, "__a__ done")
        self.assertEqual(result.limit_reason, "cycle")
        self.assertEqual(result.replacement_count, 2)

    def test_fatal_budget_reason_takes_precedence_over_cycle_diagnostic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.txt").write_text("__a__\n", encoding="utf-8")
            (root / "b.txt").write_text("done\n", encoding="utf-8")

            result = expand_wildcards(
                "__a__ __b__",
                seed=0,
                roots=[root],
                budget=WildcardExpansionBudget(max_replacements=0),
            )

        self.assertEqual(result.text, "__a__ __b__")
        self.assertEqual(result.limit_reason, "max_replacements")
        self.assertEqual(result.replacement_count, 0)

    def test_indirect_cycle_reports_the_same_reason_and_count(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.txt").write_text("__b__\n", encoding="utf-8")
            (root / "b.txt").write_text("__a__\n", encoding="utf-8")

            first = expand_wildcards("__a__", seed=0, roots=[root])
            second = expand_wildcards("__a__", seed=0, roots=[root])

        self.assertEqual(first, second)
        self.assertEqual(first.text, "__b__")
        self.assertEqual(first.limit_reason, "cycle")
        self.assertEqual(first.replacement_count, 1)

    def test_five_level_nested_wildcard_expands_normally(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for current, following in zip("abcde", ("b", "c", "d", "e", None)):
                value = f"__{following}__" if following is not None else "finished"
                (root / f"{current}.txt").write_text(f"{value}\n", encoding="utf-8")

            result = expand_wildcards("__a__", seed=0, roots=[root])

        self.assertEqual(result.text, "finished")
        self.assertIsNone(result.limit_reason)
        self.assertEqual(result.replacement_count, 5)

    def test_depth_and_replacement_limits_leave_deterministic_tokens(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.txt").write_text("__b__ __b__\n", encoding="utf-8")
            (root / "b.txt").write_text("__c__\n", encoding="utf-8")
            (root / "c.txt").write_text("finished\n", encoding="utf-8")

            depth_limited = expand_wildcards(
                "__b__",
                seed=0,
                roots=[root],
                budget=WildcardExpansionBudget(max_depth=1),
            )
            replacement_limited = expand_wildcards(
                "__a__",
                seed=0,
                roots=[root],
                budget=WildcardExpansionBudget(max_replacements=2),
            )
            repeated_replacement_limit = expand_wildcards(
                "__a__",
                seed=0,
                roots=[root],
                budget=WildcardExpansionBudget(max_replacements=2),
            )

        self.assertEqual(depth_limited.text, "__c__")
        self.assertEqual(depth_limited.limit_reason, "max_depth")
        self.assertEqual(depth_limited.replacement_count, 1)
        self.assertEqual(replacement_limited.text, "__c__ __b__")
        self.assertEqual(replacement_limited.limit_reason, "max_replacements")
        self.assertEqual(replacement_limited.replacement_count, 2)
        self.assertEqual(replacement_limited, repeated_replacement_limit)

    def test_expansion_budget_clamps_callers_to_explicit_hard_caps(self):
        budget = WildcardExpansionBudget(
            max_depth=10**9,
            max_replacements=10**9,
            max_output_chars=10**9,
            max_growth_per_pass=10**9,
        )

        self.assertEqual(budget.max_depth, wildcard_engine.MAX_EXPANSION_DEPTH)
        self.assertEqual(budget.max_replacements, wildcard_engine.MAX_EXPANSION_REPLACEMENTS)
        self.assertEqual(budget.max_output_chars, wildcard_engine.MAX_EXPANSION_OUTPUT_CHARS)
        self.assertEqual(
            budget.max_growth_per_pass,
            wildcard_engine.MAX_EXPANSION_GROWTH_PER_PASS,
        )

    def test_output_and_growth_limits_check_candidates_before_append(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "unicode.txt").write_text(f"{'가' * 5}\n", encoding="utf-8")
            (root / "growth.txt").write_text(f"{'x' * 21}\n", encoding="utf-8")

            output_limited = expand_wildcards(
                "__unicode__",
                seed=0,
                roots=[root],
                budget=WildcardExpansionBudget(max_output_chars=12),
            )
            growth_limited = expand_wildcards(
                "__growth__",
                seed=0,
                roots=[root],
                budget=WildcardExpansionBudget(
                    max_output_chars=100,
                    max_growth_per_pass=2.0,
                ),
            )

        self.assertEqual(output_limited.text, "__unicode__")
        self.assertEqual(output_limited.limit_reason, "max_output_chars")
        self.assertEqual(output_limited.replacement_count, 0)
        self.assertLessEqual(len(output_limited.text), 12)
        self.assertLessEqual(len(output_limited.text.encode("utf-8")), 12)
        self.assertEqual(growth_limited.text, "__growth__")
        self.assertEqual(growth_limited.limit_reason, "max_growth_per_pass")
        self.assertEqual(growth_limited.replacement_count, 0)

    def test_random_mode_uses_numpy_pcg64_golden_outputs(self):
        selector = wildcard_engine._Selector(7, sequential=False)
        self.assertIsInstance(selector.rng.bit_generator, wildcard_engine.np.random.PCG64)

        cases = (
            ("option_count_one", "{only}", "only"),
            ("option_count_two", "{red|blue}", "blue"),
            (
                "larger_option_count",
                "{" + "|".join(f"item-{index:02d}" for index in range(16)) + "}",
                "item-10",
            ),
            (
                "existing_combined_expansion",
                "{2$$red|blue|green}, {soft|hard}",
                "blue, green, hard",
            ),
        )

        for name, source, expected in cases:
            with self.subTest(name=name):
                first = expand_wildcards(source, seed=7)
                second = expand_wildcards(source, seed=7)

                self.assertEqual(first.text, expected)
                self.assertEqual(first, second)
                self.assertIsNone(first.limit_reason)

    def test_random_mode_weighted_and_multiselect_golden_outputs(self):
        cases = (
            ("weighted", "{1::red|3::blue|6::green}", "green"),
            (
                "multiselect_without_replacement",
                "{3$$red|blue|green|gold|silver}",
                "gold, silver, red",
            ),
            (
                "all_zero_weights_use_full_pool",
                "{5$$0::red|0::blue|0::green}",
                "red, blue, green",
            ),
        )

        for name, source, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(expand_wildcards(source, seed=7).text, expected)

    def test_ordered_texts_share_one_deterministic_selector_stream(self):
        first = expand_wildcard_texts(
            ["{red|blue|green}", "{red|blue|green}"],
            seed=7,
        )
        second = expand_wildcard_texts(
            ["{red|blue|green}", "{red|blue|green}"],
            seed=7,
        )

        self.assertEqual(first, second)
        self.assertEqual([result.text for result in first], ["blue", "green"])
        self.assertEqual(
            expand_wildcard_texts(["{red|blue|green}"], seed=7)[0],
            expand_wildcards("{red|blue|green}", seed=7),
        )
        nested = expand_wildcard_texts(
            ["{{red|blue}|green}", "{circle|square|triangle}"],
            seed=7,
        )
        self.assertEqual(
            [result.text for result in nested],
            ["green", "triangle"],
        )

    def test_ordered_file_wildcards_share_seed_stream_and_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "inner.txt").write_text(
                "circle\nsquare\ntriangle\n",
                encoding="utf-8",
            )
            (root / "outer.txt").write_text(
                "__inner__ red\n__inner__ blue\n",
                encoding="utf-8",
            )

            first = expand_wildcard_texts(
                ["__outer__", "__outer__"],
                seed=7,
                roots=[root],
            )
            second = expand_wildcard_texts(
                ["__outer__", "__outer__"],
                seed=7,
                roots=[root],
            )

        self.assertEqual(first, second)
        self.assertEqual(
            [result.text for result in first],
            ["triangle blue", "circle blue"],
        )
        for result in first:
            self.assertEqual(result.used_keys, ("outer", "inner"))
            self.assertEqual(result.replacement_count, 2)

    def test_random_mode_nested_wildcard_has_golden_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "outer.txt").write_text(
                "__inner__ red\n__inner__ blue\n",
                encoding="utf-8",
            )
            (root / "inner.txt").write_text(
                "circle\nsquare\ntriangle\n",
                encoding="utf-8",
            )

            result = expand_wildcards("__outer__", seed=7, roots=[root])

        self.assertEqual(result.text, "triangle blue")
        self.assertEqual(result.replacement_count, 2)

    def test_random_multiselect_excludes_zero_weight_options(self):
        result = expand_wildcards("{2$$0::zero|1::positive}", seed=0)

        self.assertEqual(result.text, "positive")

    def test_sequential_multiselect_keeps_zero_weight_candidates(self):
        result = expand_wildcards(
            "{3$$0::zero|1::positive}",
            seed=0,
            mode="순차",
        )

        self.assertEqual(result.text, "zero, positive")

    def test_malformed_count_ranges_preserve_the_original_expression(self):
        for source in (
            "{a-b$$red|blue}",
            "{1-x$$red|blue}",
            "{-x$$red|blue}",
            "{1-2-3$$red|blue}",
        ):
            with self.subTest(source=source):
                result = expand_wildcards(source, seed=0)

            self.assertEqual(result.text, source)
            self.assertFalse(result.changed)

    def test_deep_yaml_leaf_is_aggregated_once_per_parent_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lines = [f"{'  ' * depth}level-{depth}:" for depth in range(10)]
            lines.append(f"{'  ' * 10}- only-leaf")
            (root / "deep.yaml").write_text("\n".join(lines), encoding="utf-8")

            mapping = wildcard_engine._load_wildcard_map([root])

        for depth in range(10):
            alias = "/".join(f"level-{index}" for index in range(depth + 1))
            with self.subTest(alias=alias):
                self.assertEqual([option.text for option in mapping[alias]], ["only-leaf"])

    def test_yaml_parent_aggregation_preserves_siblings_and_explicit_duplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "weighted.yaml").write_text(
                "root:\n"
                "  branch-a:\n"
                "    leaf: [same, same]\n"
                "  branch-b:\n"
                "    leaf: [same]\n",
                encoding="utf-8",
            )

            mapping = wildcard_engine._load_wildcard_map([root])

        self.assertEqual(
            [option.text for option in mapping["root/branch-a/leaf"]],
            ["same", "same"],
        )
        self.assertEqual(
            [option.text for option in mapping["root/branch-b/leaf"]],
            ["same"],
        )
        self.assertEqual(
            [option.text for option in mapping["root"]],
            ["same", "same", "same"],
        )

    def test_unchanged_list_signature_and_expand_reuse_one_yaml_parse(self):
        self.assertIsNotNone(wildcard_engine.yaml)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "colors.yaml").write_text("colors: [red]\n", encoding="utf-8")

            with patch.object(
                wildcard_engine.yaml,
                "safe_load",
                wraps=wildcard_engine.yaml.safe_load,
            ) as safe_load:
                first_list = list_wildcards(roots=[root])
                first_signature = wildcard_engine.wildcard_sources_signature(roots=[root])
                first_expansion = expand_wildcards("__colors__", seed=0, roots=[root])
                second_list = list_wildcards(roots=[root])
                second_signature = wildcard_engine.wildcard_sources_signature(roots=[root])
                second_expansion = expand_wildcards("__colors__", seed=0, roots=[root])

        self.assertEqual(safe_load.call_count, 1)
        self.assertEqual(first_list, second_list)
        self.assertEqual(first_signature, second_signature)
        self.assertEqual(first_expansion, second_expansion)

    def test_snapshot_cache_key_preserves_root_identity_and_order(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            left = base / "left"
            right = base / "right"
            left.mkdir()
            right.mkdir()
            (left / "style.txt").write_text("left\n", encoding="utf-8")
            (right / "style.txt").write_text("right\n", encoding="utf-8")

            left_first = expand_wildcards("__style__", seed=0, roots=[left, right])
            right_first = expand_wildcards("__style__", seed=0, roots=[right, left])
            left_signature = wildcard_engine.wildcard_sources_signature(roots=[left, right])
            right_signature = wildcard_engine.wildcard_sources_signature(roots=[right, left])

        self.assertEqual(left_first.text, "left")
        self.assertEqual(right_first.text, "right")
        self.assertEqual(left_signature["roots"], [str(left), str(right)])
        self.assertEqual(right_signature["roots"], [str(right), str(left)])

    def test_runtime_library_reuses_snapshot_mapping_and_helper_returns_mutable_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "color.txt").write_text("red\nblue\ngreen\n", encoding="utf-8")
            snapshot = wildcard_engine._wildcard_snapshot([root])

            with patch.object(
                wildcard_engine,
                "_load_wildcard_map",
                side_effect=AssertionError("runtime library copied the snapshot mapping"),
            ):
                library = wildcard_engine._WildcardLibrary([root])

            exact_options = library.options_for("color")
            mutable_copy = wildcard_engine._load_wildcard_map([root])
            mutable_copy["color"].append(wildcard_engine.WildcardOption("mutated"))
            first = expand_wildcards("{2$$__color__}", seed=7, roots=[root])
            second = expand_wildcards("{2$$__color__}", seed=7, roots=[root])

        self.assertIs(library.mapping, snapshot.mapping)
        self.assertIs(exact_options, snapshot.mapping["color"])
        self.assertIsInstance(exact_options, tuple)
        self.assertIsInstance(mutable_copy, dict)
        self.assertIsInstance(mutable_copy["color"], list)
        self.assertEqual(len(mutable_copy["color"]), 4)
        self.assertEqual(len(snapshot.mapping["color"]), 3)
        self.assertEqual(first, second)
        self.assertNotIn("mutated", first.text)

    def test_yaml_snapshot_refreshes_after_add_modify_and_delete(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            colors = root / "colors.yaml"
            shapes = root / "shapes.yaml"
            colors.write_text("colors: [red]\n", encoding="utf-8")

            initial_signature = wildcard_engine.wildcard_sources_signature(roots=[root])
            initial = expand_wildcards("__colors__", seed=0, roots=[root])

            colors.write_text("colors: [blue, green]\n", encoding="utf-8")
            modified_signature = wildcard_engine.wildcard_sources_signature(roots=[root])
            modified = expand_wildcards(
                "__colors__",
                seed=0,
                mode="sequential",
                roots=[root],
            )

            shapes.write_text("shapes: [circle]\n", encoding="utf-8")
            after_add = list_wildcards(roots=[root])

            colors.unlink()
            after_delete = list_wildcards(roots=[root])
            missing = expand_wildcards("__colors__", seed=0, roots=[root])

        self.assertEqual(initial.text, "red")
        self.assertNotEqual(initial_signature, modified_signature)
        self.assertEqual(modified.text, "blue")
        self.assertEqual(after_add, ["colors", "shapes"])
        self.assertEqual(after_delete, ["shapes"])
        self.assertEqual(missing.text, "__colors__")
        self.assertEqual(missing.missing_keys, ("colors",))

    def test_transient_loader_oserror_is_not_cached(self):
        original_loader = wildcard_engine._load_wildcard_file
        attempts = []

        def flaky_loader(root, path):
            attempts.append(path)
            if len(attempts) == 1:
                raise OSError("transient read failure")
            return original_loader(root, path)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "color.txt").write_text("red\n", encoding="utf-8")
            cache_key = wildcard_engine._scan_wildcard_sources((root,)).cache_key

            with patch.object(
                wildcard_engine,
                "_load_wildcard_file",
                side_effect=flaky_loader,
            ) as loader:
                first = expand_wildcards("__color__", seed=0, roots=[root])
                with wildcard_engine._SNAPSHOT_CONDITION:
                    self.assertNotIn(cache_key, wildcard_engine._SNAPSHOT_CACHE)
                    self.assertNotIn(cache_key, wildcard_engine._SNAPSHOT_BUILDING)
                second = expand_wildcards("__color__", seed=0, roots=[root])

        self.assertEqual(first.text, "__color__")
        self.assertEqual(second.text, "red")
        self.assertEqual(loader.call_count, 2)

    def test_invalid_yaml_parse_remains_cacheable_as_empty(self):
        self.assertIsNotNone(wildcard_engine.yaml)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "invalid.yaml").write_text("color: [red\n", encoding="utf-8")
            cache_key = wildcard_engine._scan_wildcard_sources((root,)).cache_key

            with patch.object(
                wildcard_engine.yaml,
                "safe_load",
                wraps=wildcard_engine.yaml.safe_load,
            ) as safe_load:
                first = expand_wildcards("__color__", seed=0, roots=[root])
                second = expand_wildcards("__color__", seed=0, roots=[root])

            with wildcard_engine._SNAPSHOT_CONDITION:
                self.assertIn(cache_key, wildcard_engine._SNAPSHOT_CACHE)

        self.assertEqual(first.text, "__color__")
        self.assertEqual(second.text, "__color__")
        self.assertEqual(safe_load.call_count, 1)

    def test_persistent_yaml_read_oserror_never_caches_or_leaves_building_key(self):
        read_started = threading.Event()
        release_read = threading.Event()
        waiter_entered = threading.Event()
        read_calls = []
        original_wait = wildcard_engine._SNAPSHOT_CONDITION.wait

        def unreadable_yaml(path):
            read_calls.append(path)
            if len(read_calls) == 1:
                read_started.set()
                if not release_read.wait(5):
                    raise AssertionError("timed out waiting for parallel wildcard request")
            raise OSError("persistent read failure")

        def observed_wait(timeout=None):
            waiter_entered.set()
            return original_wait(timeout)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "library.yaml").write_text("color: [red]\n", encoding="utf-8")
            cache_key = wildcard_engine._scan_wildcard_sources((root,)).cache_key

            with patch.object(
                wildcard_engine,
                "_read_text_file",
                side_effect=unreadable_yaml,
            ), patch.object(
                wildcard_engine._SNAPSHOT_CONDITION,
                "wait",
                side_effect=observed_wait,
            ), ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(
                    expand_wildcards,
                    "__color__",
                    seed=0,
                    roots=[root],
                )
                try:
                    self.assertTrue(read_started.wait(5))
                    second = executor.submit(
                        expand_wildcards,
                        "__color__",
                        seed=0,
                        roots=[root],
                    )
                    self.assertTrue(waiter_entered.wait(5))
                finally:
                    release_read.set()
                first_result = first.result(timeout=5)
                second_result = second.result(timeout=5)

            with wildcard_engine._SNAPSHOT_CONDITION:
                self.assertNotIn(cache_key, wildcard_engine._SNAPSHOT_CACHE)
                self.assertNotIn(cache_key, wildcard_engine._SNAPSHOT_BUILDING)

        self.assertEqual(first_result.text, "__color__")
        self.assertEqual(second_result.text, "__color__")
        self.assertEqual(len(read_calls), 2)

    def test_file_change_during_build_retries_before_publish(self):
        build_started = threading.Event()
        release_build = threading.Event()
        build_calls = []
        original_build = wildcard_engine._build_wildcard_snapshot

        def blocked_first_build(source_state):
            snapshot = original_build(source_state)
            build_calls.append(source_state.cache_key)
            if len(build_calls) == 1:
                build_started.set()
                if not release_build.wait(5):
                    raise AssertionError("timed out waiting to mutate wildcard source")
            return snapshot

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            colors = root / "colors.yaml"
            colors.write_text("colors: [red]\n", encoding="utf-8")

            with patch.object(
                wildcard_engine,
                "_build_wildcard_snapshot",
                side_effect=blocked_first_build,
            ), ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    expand_wildcards,
                    "__colors__",
                    seed=0,
                    roots=[root],
                )
                try:
                    self.assertTrue(build_started.wait(5))
                    colors.write_text("colors: [blue-new]\n", encoding="utf-8")
                finally:
                    release_build.set()
                result = future.result(timeout=5)

        self.assertEqual(result.text, "blue-new")
        self.assertEqual(len(build_calls), 2)

    def test_parallel_same_key_build_is_single_flight_and_atomically_published(self):
        build_ready = threading.Event()
        release_build = threading.Event()
        waiter_entered = threading.Event()
        build_calls = []
        original_build = wildcard_engine._build_wildcard_snapshot
        original_wait = wildcard_engine._SNAPSHOT_CONDITION.wait

        def blocked_build(source_state):
            snapshot = original_build(source_state)
            build_calls.append(source_state.cache_key)
            build_ready.set()
            if not release_build.wait(5):
                raise AssertionError("timed out waiting for parallel wildcard request")
            return snapshot

        def observed_wait(timeout=None):
            waiter_entered.set()
            return original_wait(timeout)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "library.yaml").write_text(
                "alpha: [one]\nbeta: [two]\n",
                encoding="utf-8",
            )

            with patch.object(
                wildcard_engine,
                "_build_wildcard_snapshot",
                side_effect=blocked_build,
            ), patch.object(
                wildcard_engine._SNAPSHOT_CONDITION,
                "wait",
                side_effect=observed_wait,
            ), ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(list_wildcards, roots=[root])
                try:
                    self.assertTrue(build_ready.wait(5))
                    with wildcard_engine._SNAPSHOT_CONDITION:
                        self.assertFalse(
                            any(
                                snapshot.roots == (str(root),)
                                for snapshot in wildcard_engine._SNAPSHOT_CACHE.values()
                            )
                        )
                    second = executor.submit(list_wildcards, roots=[root])
                    self.assertTrue(waiter_entered.wait(5))
                    self.assertFalse(first.done())
                    self.assertFalse(second.done())
                finally:
                    release_build.set()
                first_result = first.result(timeout=5)
                second_result = second.result(timeout=5)

        self.assertEqual(len(build_calls), 1)
        self.assertEqual(first_result, ["alpha", "beta"])
        self.assertEqual(second_result, ["alpha", "beta"])

    def test_list_wildcards_returns_relative_keys_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "style.txt").write_text("painterly\n", encoding="utf-8")

            items = list_wildcards(roots=[root])

        self.assertEqual(items, ["style"])

    def test_korean_wildcard_keys_can_be_listed_and_expanded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "하츠.txt").write_text("hatsune option\n", encoding="utf-8")

            items = list_wildcards(roots=[root])
            result = expand_wildcards("__하츠__", seed=0, roots=[root])

        self.assertEqual(items, ["하츠"])
        self.assertEqual(result.text, "hatsune option")


class WildcardSeedContractTests(unittest.TestCase):
    def test_public_seed_controls_share_the_javascript_safe_range(self):
        public_max = wildcard_engine.PUBLIC_MAX_SEED

        self.assertEqual(public_max, (1 << 53) - 1)
        self.assertEqual(wildcard_engine.next_seed(0, "fixed"), 0)
        self.assertEqual(wildcard_engine.next_seed(public_max, "fixed"), public_max)
        self.assertEqual(wildcard_engine.next_seed(public_max, "increment"), 0)
        self.assertEqual(wildcard_engine.next_seed(0, "decrement"), public_max)
        self.assertEqual(
            wildcard_engine.next_seed(public_max, "decrement"),
            public_max - 1,
        )
        with patch("wildcard_engine.random.SystemRandom") as system_random:
            system_random.return_value.randrange.return_value = public_max

            self.assertEqual(
                wildcard_engine.next_seed(123, "randomize"),
                public_max,
            )

            system_random.return_value.randrange.assert_called_once_with(
                0,
                public_max + 1,
            )

    def test_legacy_uint64_seed_is_preserved_until_a_control_advances_it(self):
        public_max = wildcard_engine.PUBLIC_MAX_SEED
        legacy_max = wildcard_engine.MAX_SEED

        self.assertEqual(wildcard_engine.normalize_seed(legacy_max), legacy_max)
        self.assertEqual(wildcard_engine.normalize_seed(legacy_max + 1), legacy_max)
        self.assertEqual(wildcard_engine.next_seed(legacy_max, "fixed"), legacy_max)
        self.assertEqual(wildcard_engine.next_seed(legacy_max + 1, "fixed"), legacy_max)
        self.assertEqual(wildcard_engine.next_seed(legacy_max, "increment"), 0)
        self.assertEqual(
            wildcard_engine.next_seed(legacy_max, "decrement"),
            public_max - 1,
        )

    def test_node_inputs_advertise_public_range_without_rejecting_legacy_workflows(self):
        node_inputs = (
            (EasyUseAnimaWildcard, "seed"),
            (EasyUseAnimaPromptStudioAdvanced, "wildcard_seed"),
            (EasyUseAnimaPromptStudioRegional, "wildcard_seed"),
        )

        for node_class, input_name in node_inputs:
            with self.subTest(node=node_class.__name__):
                _input_type, config = node_class.INPUT_TYPES()["required"][input_name]
                self.assertEqual(config["max"], wildcard_engine.MAX_SEED)
                self.assertIn(str(wildcard_engine.PUBLIC_MAX_SEED), config["tooltip"])
                self.assertIn("legacy", config["tooltip"].lower())

    def test_prompt_studio_modes_own_seed_progression(self):
        wildcard = EasyUseAnimaWildcard().generate(
            "",
            "",
            "일반",
            0,
        )
        advanced = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            "[]",
            wildcard_mode="일반",
            wildcard_seed=0,
            wildcard_seed_after_generate="decrement",
        )
        regional = EasyUseAnimaPromptStudioRegional().build(
            "[]",
            "{}",
            wildcard_mode="순차",
            wildcard_seed=0,
            wildcard_seed_after_generate="decrement",
        )

        self.assertEqual(wildcard["ui"]["wildcard"][0]["seed"], 0)
        self.assertEqual(
            advanced["ui"]["prompt_studio_advanced"][0]["wildcard_seed"],
            0,
        )
        self.assertEqual(
            regional["ui"]["prompt_studio_regional"][0]["wildcard_seed"],
            1,
        )

    def test_legacy_current_seed_is_used_before_next_seed_reenters_public_range(self):
        legacy_max = wildcard_engine.MAX_SEED
        expansion = WildcardExpansionResult(
            text="expanded style",
            changed=True,
            used_keys=("style",),
            missing_keys=(),
        )

        with patch("nodes.expand_wildcards", return_value=expansion) as expand:
            result = EasyUseAnimaWildcard().generate(
                "__style__",
                "",
                "일반",
                legacy_max,
            )

        self.assertEqual(expand.call_args.kwargs["seed"], legacy_max)
        self.assertEqual(result["result"], ("expanded style", legacy_max))


class WildcardNodeTests(unittest.TestCase):
    def test_prompt_studio_fields_share_one_seed_stream(self):
        fields = [
            {
                "id": "positive_first",
                "pane": "positive",
                "type": "general",
                "text": "{red|blue|green}",
                "enabled": True,
            },
            {
                "id": "positive_second",
                "pane": "positive",
                "type": "general",
                "text": "{red|blue|green}",
                "enabled": True,
            },
        ]

        expanded, metadata = nodes_module._expand_advanced_wildcard_fields(
            fields,
            7,
            "일반",
        )

        self.assertEqual(
            [field["text"] for field in expanded],
            ["blue", "green"],
        )
        self.assertTrue(metadata["changed"])

    def test_prompt_studio_general_expands_samples_flower_deterministically(self):
        source_fields = [{
            "id": "positive_general",
            "pane": "positive",
            "type": "general",
            "text": "__samples/flower__",
            "enabled": True,
        }]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            samples = root / "samples"
            samples.mkdir()
            (samples / "flower.txt").write_text(
                "rose\ntulip\nsunflower\n",
                encoding="utf-8",
            )

            def expand_from_test_root(texts, *, seed, mode):
                return expand_wildcard_texts(texts, seed=seed, mode=mode, roots=[root])

            with patch(
                "nodes.expand_wildcard_texts",
                side_effect=expand_from_test_root,
            ):
                first, _ = nodes_module._expand_advanced_wildcard_fields(
                    source_fields,
                    5,
                    "일반",
                )
                second, _ = nodes_module._expand_advanced_wildcard_fields(
                    source_fields,
                    5,
                    "일반",
                )

        self.assertEqual(first, second)
        self.assertIn(first[0]["text"], {"rose", "tulip", "sunflower"})
        self.assertNotEqual(first[0]["text"], "samples/flower")
        self.assertEqual(source_fields[0]["text"], "__samples/flower__")

    def test_prompt_studio_sequential_seed_selects_and_wraps_in_order(self):
        fields = [{
            "id": "positive_general",
            "pane": "positive",
            "type": "general",
            "text": "{rose|tulip|sunflower}",
            "enabled": True,
        }]

        outputs = [
            nodes_module._expand_advanced_wildcard_fields(fields, seed, "순차")[0][0]["text"]
            for seed in (0, 1, 2, 3, 1)
        ]

        self.assertEqual(outputs, ["rose", "tulip", "sunflower", "rose", "tulip"])

    def test_connected_field_uses_shared_rng_without_replacing_saved_sources(self):
        saved_source = [
            {
                "id": "positive_connected",
                "pane": "positive",
                "type": "general",
                "text": "stored fallback",
                "enabled": True,
            },
            {
                "id": "positive_local",
                "pane": "positive",
                "type": "general",
                "text": "{red|blue|green}",
                "enabled": True,
            },
        ]
        field_inputs = {
            "field_positive_connected": "{cat|dog|fox}",
        }
        effective_source = nodes_module._apply_advanced_field_inputs(
            saved_source,
            field_inputs,
        )
        effective_fields, _effective_metadata = nodes_module._expand_advanced_wildcard_fields(
            effective_source,
            17,
            "일반",
        )

        self.assertEqual(
            [field["text"] for field in effective_fields],
            ["fox", "red"],
        )
        self.assertEqual(
            [field["text"] for field in saved_source],
            ["stored fallback", "{red|blue|green}"],
        )

    def test_input_tooltips_cover_populated_text_and_deterministic_modes(self):
        inputs = EasyUseAnimaWildcard.INPUT_TYPES()["required"]
        text_tooltip = inputs["text"][1]["tooltip"]
        for syntax in (
            "__name__",
            "{a|b|c}",
            "N::item",
            "{n$$...}",
            "{min-max$$separator$$...}",
            "N#__name__",
            "nested",
            "ignore case",
            "* glob",
            "#",
        ):
            with self.subTest(syntax=syntax):
                self.assertIn(syntax, text_tooltip)

        populated_tooltip = inputs["populated_text"][1]["tooltip"]
        self.assertIn("Impact Pack's populated_text", populated_tooltip)
        self.assertIn("Fixed ignores text", populated_tooltip)
        self.assertIn("file wildcards", populated_tooltip)

        mode_tooltip = inputs["mode"][1]["tooltip"]
        self.assertIn("General (일반)", mode_tooltip)
        self.assertIn("Fixed (고정)", mode_tooltip)
        self.assertIn("Saved workflows serialize", mode_tooltip)

        seed_tooltip = inputs["seed"][1]["tooltip"]
        self.assertIn("same text and seed", seed_tooltip.lower())
        self.assertNotIn("seed_after_generate", inputs)

    def test_native_wildcard_uses_populated_text_without_duplicate_seed_control(self):
        self.assertEqual(
            EasyUseAnimaWildcard.INPUT_TYPES()["required"]["mode"][0],
            ("일반", "고정"),
        )
        self.assertNotIn(
            "seed_after_generate",
            EasyUseAnimaWildcard.INPUT_TYPES()["required"],
        )
        self.assertIs(
            EasyUseAnimaWildcard.INPUT_TYPES()["required"]["seed"][1]["control_after_generate"],
            True,
        )
        workflow_prompt = {
            "7": {
                "inputs": {
                    "text": "__style__",
                    "populated_text": "",
                    "mode": "일반",
                    "seed": 2,
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [{
                    "id": 7,
                    "widgets_values": ["__style__", "", "일반", 2, "randomize"],
                }]
            }
        }

        with (
            patch(
                "nodes.expand_wildcards",
                return_value=WildcardExpansionResult(
                    text="expanded style",
                    changed=True,
                    used_keys=("style",),
                    missing_keys=(),
                ),
            ),
        ):
            result = EasyUseAnimaWildcard().generate(
                "__style__",
                "",
                "일반",
                2,
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="7",
            )

        self.assertEqual(result["result"], ("expanded style", 2))
        self.assertEqual(result["ui"]["wildcard"][0]["seed"], 2)
        self.assertEqual(workflow_prompt["7"]["inputs"]["seed"], 2)
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][3], 2)
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][4], "fixed")

    def test_node_stores_fixed_populated_metadata_for_saved_workflow(self):
        workflow_prompt = {
            "7": {
                "inputs": {
                    "text": "__style__",
                    "populated_text": "",
                    "mode": "일반",
                    "seed": 5,
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 7,
                        "widgets_values": ["__style__", "", "일반", 5, "increment"],
                    }
                ]
            }
        }

        with patch(
            "nodes.expand_wildcards",
            return_value=WildcardExpansionResult(
                text="expanded style",
                changed=True,
                used_keys=("style",),
                missing_keys=(),
            ),
        ):
            result = EasyUseAnimaWildcard().generate(
                "__style__",
                "",
                "일반",
                5,
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="7",
            )

        self.assertEqual(result["result"], ("expanded style", 5))
        self.assertEqual(workflow_prompt["7"]["inputs"]["populated_text"], "expanded style")
        self.assertEqual(workflow_prompt["7"]["inputs"]["mode"], "고정")
        self.assertEqual(workflow_prompt["7"]["inputs"]["seed"], 5)
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][1], "expanded style")
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][2], "고정")
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][3], 5)
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][4], "fixed")

    def test_fixed_mode_expands_inline_multiselect(self):
        result = EasyUseAnimaWildcard().generate(
            "ignored source",
            "{2$$red|blue|green}",
            "고정",
            0,
        )

        self.assertNotEqual(result["result"][0], "{2$$red|blue|green}")
        self.assertEqual(len([part.strip() for part in result["result"][0].split(",")]), 2)
        self.assertEqual(result["ui"]["wildcard"][0]["status"], "fixed")

    def test_native_fixed_uses_populated_text_and_current_seed(self):
        with patch(
            "nodes.expand_wildcards",
            return_value=WildcardExpansionResult(
                text="expanded style",
                changed=False,
                used_keys=(),
                missing_keys=(),
            ),
        ) as expand:
            result = EasyUseAnimaWildcard().generate(
                "__style__",
                "expanded style",
                "고정",
                5,
            )

        expand.assert_called_once_with("expanded style", seed=5, mode="fixed")
        self.assertEqual(result["result"], ("expanded style", 5))
        self.assertEqual(result["ui"]["wildcard"][0]["status"], "fixed")

    def test_native_fixed_keeps_empty_populated_text_empty(self):
        with patch(
            "nodes.expand_wildcards",
            return_value=WildcardExpansionResult(
                text="",
                changed=False,
                used_keys=(),
                missing_keys=(),
            ),
        ) as expand:
            result = EasyUseAnimaWildcard().generate(
                "__style__",
                "",
                "고정",
                5,
            )

        expand.assert_called_once_with("", seed=5, mode="fixed")
        self.assertEqual(result["result"], ("", 5))

    def test_native_fixed_expands_samples_flower_and_repeats_same_seed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            samples = root / "samples"
            samples.mkdir()
            (samples / "flower.txt").write_text(
                "rose\ntulip\nsunflower\n",
                encoding="utf-8",
            )

            def expand_from_test_root(text, *, seed, mode):
                return expand_wildcards(text, seed=seed, mode=mode, roots=[root])

            with patch("nodes.expand_wildcards", side_effect=expand_from_test_root) as expand:
                first = EasyUseAnimaWildcard().generate(
                    "ignored source",
                    "__samples/flower__",
                    "고정",
                    5,
                )
                second = EasyUseAnimaWildcard().generate(
                    "ignored source",
                    "__samples/flower__",
                    "고정",
                    5,
                )

        self.assertEqual(expand.call_count, 2)
        for call in expand.call_args_list:
            self.assertEqual(call.args, ("__samples/flower__",))
            self.assertEqual(call.kwargs, {"seed": 5, "mode": "fixed"})
        self.assertEqual(first["result"], second["result"])
        self.assertIn(first["result"][0], {"rose", "tulip", "sunflower"})
        self.assertNotEqual(first["result"][0], "samples/flower")
        self.assertEqual(first["result"][1], 5)
        self.assertEqual(first["ui"]["wildcard"][0]["used_keys"], ["samples/flower"])

    def test_prompt_studio_legacy_reproduce_normalizes_to_general_fixed_seed(self):
        fields = [{
            "id": "positive_general",
            "pane": "positive",
            "type": "general",
            "label": "General Tags",
            "text": "expanded style",
            "height": 120,
            "enabled": True,
        }]

        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
            wildcard_mode="재현",
            wildcard_seed=5,
            wildcard_seed_after_generate="increment",
        )

        payload = result["ui"]["prompt_studio_advanced"][0]
        self.assertEqual(result["result"][0], "expanded style")
        self.assertEqual(payload["wildcard_mode"], "일반")
        self.assertEqual(payload["wildcard_seed"], 5)
        self.assertEqual(payload["wildcard_seed_after_generate"], "fixed")
        self.assertEqual(
            json.loads(payload["advanced_fields"])[0]["text"],
            "expanded style",
        )

    def _assert_advanced_connected_wildcard_round_trip(self, node_class):
        source_text = "{cat|dog|fox}"
        fields = [{
            "id": "positive_general",
            "pane": "positive",
            "type": "general",
            "label": "General Tags",
            "text": "stored fallback",
            "height": 120,
            "enabled": True,
        }]
        fields_json = json.dumps(fields)
        workflow_prompt = {
            "9": {
                "inputs": {
                    "advanced_fields": fields_json,
                    "wildcard_mode": "일반",
                    "wildcard_seed": 17,
                    "wildcard_seed_after_generate": "fixed",
                    "field_positive_general": ["8", 0],
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [{
                    "id": 9,
                    "widgets_values": [
                        False,
                        True,
                        False,
                        "1024",
                        "1024 * 1024 (1:1)",
                        1024,
                        1024,
                        False,
                        fields_json,
                        False,
                        "일반",
                        17,
                        "fixed",
                    ],
                }]
            }
        }

        initial = node_class().build(
            False,
            True,
            False,
            False,
            fields_json,
            wildcard_mode="일반",
            wildcard_seed=17,
            wildcard_seed_after_generate="fixed",
            workflow_prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
            unique_id="9",
            field_positive_general=source_text,
        )

        ui_payload = initial["ui"]["prompt_studio_advanced"][0]
        effective_output = initial["result"][0]
        if isinstance(effective_output, dict):
            effective_output = effective_output["positive_prompt"]
        saved_prompt_fields = json.loads(workflow_prompt["9"]["inputs"]["advanced_fields"])
        saved_image_fields = json.loads(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][8])
        saved_property_fields = json.loads(
            extra_pnginfo["workflow"]["nodes"][0]["properties"]["easyuse_anima_advanced_fields"]
        )

        self.assertEqual(ui_payload["field_inputs"]["field_positive_general"], source_text)
        self.assertEqual(effective_output, "fox")
        self.assertEqual(saved_prompt_fields[0]["text"], "stored fallback")
        self.assertEqual(saved_image_fields[0]["text"], "stored fallback")
        self.assertEqual(saved_property_fields[0]["text"], "stored fallback")
        self.assertEqual(workflow_prompt["9"]["inputs"]["field_positive_general"], ["8", 0])
        self.assertEqual(workflow_prompt["9"]["inputs"]["wildcard_mode"], "일반")

        repeated = node_class().build(
            False,
            True,
            False,
            False,
            json.dumps(saved_prompt_fields),
            wildcard_mode="일반",
            wildcard_seed=17,
            wildcard_seed_after_generate="randomize",
            field_positive_general=source_text,
        )

        repeated_output = repeated["result"][0]
        if isinstance(repeated_output, dict):
            self.assertEqual(repeated_output["fields"][0]["text"], "fox")
            repeated_output = repeated_output["positive_prompt"]
        self.assertEqual(repeated_output, "fox")

    def test_prompt_studio_advanced_connected_wildcard_round_trip_preserves_expansion(self):
        self._assert_advanced_connected_wildcard_round_trip(EasyUseAnimaPromptStudioAdvanced)

    def test_prompt_studio_advanced_v2_connected_wildcard_round_trip_preserves_expansion(self):
        self._assert_advanced_connected_wildcard_round_trip(EasyUseAnimaPromptStudioAdvancedV2)

    def test_prompt_studio_advanced_legacy_reproduce_alias_keeps_plain_connected_input(self):
        fields_json = json.dumps([{
            "id": "positive_general",
            "pane": "positive",
            "type": "general",
            "label": "General Tags",
            "text": "stored fallback",
            "height": 120,
            "enabled": True,
        }])

        for node_class in (
            EasyUseAnimaPromptStudioAdvanced,
            EasyUseAnimaPromptStudioAdvancedV2,
        ):
            with self.subTest(node_class=node_class.__name__):
                reproduced = node_class().build(
                    False,
                    True,
                    False,
                    False,
                    fields_json,
                    wildcard_mode="재현",
                    wildcard_seed=17,
                    wildcard_seed_after_generate="fixed",
                    field_positive_general="plain connected",
                )

                reproduced_output = reproduced["result"][0]
                if isinstance(reproduced_output, dict):
                    reproduced_output = reproduced_output["positive_prompt"]
                self.assertEqual(reproduced_output, "plain connected")

    def test_prompt_studio_regional_connected_wildcard_round_trip_preserves_expansion(self):
        source_text = "{cat|dog|fox}"
        fields = [{
            "id": "positive_general",
            "pane": "positive",
            "type": "general",
            "label": "General Tags",
            "text": "stored fallback",
            "height": 120,
            "enabled": True,
            "mask_ids": [],
        }]
        fields_json = json.dumps(fields)
        config_json = json.dumps({})
        workflow_prompt = {
            "42": {
                "inputs": {
                    "regional_fields": fields_json,
                    "regional_config": config_json,
                    "wildcard_mode": "일반",
                    "wildcard_seed": 17,
                    "wildcard_seed_after_generate": "fixed",
                    "field_positive_general": ["41", 0],
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [{
                    "id": 42,
                    "widgets_values": [
                        fields_json,
                        config_json,
                        "1024",
                        "1024 * 1024 (1:1)",
                        1024,
                        1024,
                        "일반",
                        17,
                        "fixed",
                    ],
                    "properties": {},
                }]
            }
        }

        initial = EasyUseAnimaPromptStudioRegional().build(
            fields_json,
            config_json,
            wildcard_mode="일반",
            wildcard_seed=17,
            wildcard_seed_after_generate="fixed",
            workflow_prompt=workflow_prompt,
            extra_pnginfo=extra_pnginfo,
            unique_id="42",
            field_positive_general=source_text,
        )

        ui_payload = initial["ui"]["prompt_studio_regional"][0]
        saved_prompt_fields = json.loads(workflow_prompt["42"]["inputs"]["regional_fields"])
        saved_image_fields = json.loads(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][0])
        saved_property_fields = json.loads(
            extra_pnginfo["workflow"]["nodes"][0]["properties"]["easyuse_anima_regional_fields"]
        )
        self.assertEqual(ui_payload["field_inputs"]["field_positive_general"], source_text)
        self.assertEqual(initial["result"][0], "fox")
        self.assertEqual(saved_prompt_fields[0]["text"], "stored fallback")
        self.assertEqual(saved_image_fields[0]["text"], "stored fallback")
        self.assertEqual(saved_property_fields[0]["text"], "stored fallback")
        self.assertEqual(workflow_prompt["42"]["inputs"]["field_positive_general"], ["41", 0])
        self.assertEqual(workflow_prompt["42"]["inputs"]["wildcard_mode"], "일반")

        repeated = EasyUseAnimaPromptStudioRegional().build(
            json.dumps(saved_prompt_fields),
            config_json,
            wildcard_mode="일반",
            wildcard_seed=17,
            wildcard_seed_after_generate="randomize",
            field_positive_general=source_text,
        )

        self.assertEqual(repeated["result"][0], "fox")

    def test_prompt_studio_regional_legacy_reproduce_alias_keeps_plain_connected_input(self):
        fields_json = json.dumps([{
            "id": "positive_general",
            "pane": "positive",
            "type": "general",
            "label": "General Tags",
            "text": "stored fallback",
            "height": 120,
            "enabled": True,
            "mask_ids": [],
        }])

        reproduced = EasyUseAnimaPromptStudioRegional().build(
            fields_json,
            json.dumps({}),
            wildcard_mode="재현",
            wildcard_seed=17,
            wildcard_seed_after_generate="fixed",
            field_positive_general="plain connected",
        )

        self.assertEqual(reproduced["result"][0], "plain connected")

    def test_public_settings_include_wildcard_extra_paths(self):
        self.assertIn("wildcard.extra_paths", public_settings())

    def test_prompt_studio_advanced_preserves_source_fields_and_mode_contract(self):
        fields = [
            {
                "id": "positive_general",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "__style__",
                "height": 120,
                "enabled": True,
            }
        ]
        workflow_prompt = {
            "9": {
                "inputs": {
                    "advanced_fields": json.dumps(fields),
                    "wildcard_mode": "일반",
                    "wildcard_seed": 2,
                    "wildcard_seed_after_generate": "randomize",
                    "easyuse_anima_reserved_wildcard_next_seed": json.dumps({
                        "version": 1,
                        "current_seed": 2,
                        "next_seed": 2,
                        "mode": "populate",
                        "control": "fixed",
                    }),
                }
            }
        }
        extra_pnginfo = {
            "workflow": {
                "nodes": [
                    {
                        "id": 9,
                        "widgets_values": [
                            False,
                            True,
                            False,
                            "1024",
                            "1024 * 1024 (1:1)",
                            1024,
                            1024,
                            False,
                            json.dumps(fields),
                            False,
                            "일반",
                            2,
                            "randomize",
                        ],
                    }
                ]
            }
        }

        with patch(
            "nodes.expand_wildcard_texts",
            return_value=(WildcardExpansionResult(
                text="expanded style",
                changed=True,
                used_keys=("style",),
                missing_keys=(),
            ),),
        ):
            result = EasyUseAnimaPromptStudioAdvanced().build(
                False,
                True,
                False,
                False,
                json.dumps(fields),
                wildcard_mode="일반",
                wildcard_seed=2,
                wildcard_seed_after_generate="randomize",
                workflow_prompt=workflow_prompt,
                extra_pnginfo=extra_pnginfo,
                unique_id="9",
                easyuse_anima_reserved_wildcard_next_seed=json.dumps({
                    "version": 1,
                    "current_seed": 2,
                    "next_seed": 2,
                    "mode": "populate",
                    "control": "fixed",
                }),
            )

        payload_fields = json.loads(result["ui"]["prompt_studio_advanced"][0]["advanced_fields"])
        saved_fields = json.loads(workflow_prompt["9"]["inputs"]["advanced_fields"])
        saved_image_fields = json.loads(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][8])

        self.assertEqual(result["result"][0], "expanded style")
        self.assertEqual(payload_fields[0]["text"], "__style__")
        self.assertEqual(saved_fields[0]["text"], "__style__")
        self.assertEqual(saved_image_fields[0]["text"], "__style__")
        self.assertEqual(workflow_prompt["9"]["inputs"]["wildcard_mode"], "일반")
        self.assertEqual(workflow_prompt["9"]["inputs"]["wildcard_seed_after_generate"], "fixed")
        self.assertEqual(workflow_prompt["9"]["inputs"]["wildcard_seed"], 2)
        self.assertNotIn(
            "easyuse_anima_reserved_wildcard_next_seed",
            workflow_prompt["9"]["inputs"],
        )
        self.assertEqual(extra_pnginfo["workflow"]["nodes"][0]["widgets_values"][11], 2)
        self.assertEqual(result["ui"]["prompt_studio_advanced"][0]["wildcard_seed"], 2)

    def test_prompt_studio_legacy_fixed_mode_normalizes_to_general_and_expands(self):
        fields = [
            {
                "id": "positive_general",
                "pane": "positive",
                "type": "general",
                "label": "General Tags",
                "text": "{2$$red|blue|green}",
                "height": 120,
                "enabled": True,
            }
        ]

        result = EasyUseAnimaPromptStudioAdvanced().build(
            False,
            True,
            False,
            False,
            json.dumps(fields),
            wildcard_mode="고정",
            wildcard_seed=0,
            wildcard_seed_after_generate="fixed",
        )

        prompt = result["result"][0]
        self.assertNotEqual(prompt, "{2$$red|blue|green}")
        self.assertEqual(len([part.strip() for part in prompt.split(",")]), 2)
        self.assertEqual(result["ui"]["prompt_studio_advanced"][0]["wildcard_mode"], "일반")
        self.assertEqual(result["ui"]["prompt_studio_advanced"][0]["wildcard_seed"], 0)


if __name__ == "__main__":
    unittest.main()
