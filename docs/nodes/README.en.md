# EasyUse Anima Node Guide

This is the entry point for user-facing node documentation. For installation and
shared settings, start with the top-level [README](../../README.en.md).

## Quick Lookup

| Node | Purpose | Details |
| --- | --- | --- |
| Anima NAIA Random Prompt | Requests prompt, negative prompt, and resolution from the NAIA remote API | [Guide](anima-naia-random-prompt.en.md) |
| Anima Prompt Corrector | Normalizes comma-separated prompts into ANIMA order | [Guide](anima-prompt-corrector.en.md) |
| Anima Prompt Corrector Simple | Takes one prompt and outputs only the corrected prompt string | [Guide](anima-prompt-corrector.en.md) |
| Anima Prompt Builder | Combines multiple prompt fields into one prompt | [Guide](anima-prompt-builder.en.md) |
| Anima Prompt Studio | Adds UI editing, autocomplete, and highlighting to Prompt Builder | [Guide](anima-prompt-studio.en.md) |
| Anima Prompt Studio Advanced | Advanced editor with positive/negative fields, NAIA, resolution, and wildcard controls | [Guide](anima-prompt-studio-advanced.en.md) |
| Anima Prompt Studio Advanced v2 | v2 editor that outputs an `EASYUSE_ANIMA_PROMPT_DATA` dict | [Guide](anima-prompt-studio-advanced.en.md) |
| EASYUSE_ANIMA_PROMPT_DATA | Prompt data pass-through, overrides, and old compatibility outputs | [Guide](anima-prompt-studio-advanced.en.md) |
| Anima Prompt Data Conditioning | Builds conditioning, model patch output, and latent image from prompt data | [Guide](anima-prompt-studio-advanced.en.md) |
| Anima Artist Mix Conditioning | Outputs artist mix positive CONDITIONING from a prompt and separate artist_tags input | [Guide](anima-artist-mix-conditioning.en.md) |
| Anima Wildcard | Expands wildcard text without Prompt Studio | [Guide](anima-wildcard.en.md) |
| Anima LoRA Preset | Stores and outputs LoRA profiles, style prompts, and trigger words | [Guide](anima-lora-preset.en.md) |
| Easy Use Anima Input | Bundles ANIMA diffusion model, VAE, CLIP, and prompt data into an AiO context | [Guide](anima-aio-generator.en.md) |
| Anima AiO Generator | Runs sampling, Highres, Detailer, and saving from the prompt-data context | [Guide](anima-aio-generator.en.md) |
| Anima AiO Hook Combine | Composes AiO extension hooks in middleware order | [Developer guide](../extensions/aio-hooks.en.md) |
| Anima Image Scale By Multiple | Scales images to valid size multiples while preserving the original aspect ratio | [Guide](anima-image-scale-by-multiple.en.md) |
| Anima Detailer Align Hook | Aligns Impact detailer crop sampling sizes | [Guide](anima-detailer-align-hook.en.md) |

## Related Guides

- Wildcard syntax: [Wildcard Guide](../wildcards.en.md)
- Autocomplete CSV: [Autocomplete CSV Guide](../autocomplete-csv.en.md)
- AiO extension development: [AiO Hook API v1](../extensions/aio-hooks.en.md)
- Release changes: [RELEASE.md](../../RELEASE.md)
