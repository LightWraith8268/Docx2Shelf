"""Re-exports prompt helpers from :mod:`docx2shelf.utils`.

``cli_handlers`` modules import ``prompt``/``prompt_bool``/``prompt_select``
from ``..prompts``; the actual implementations live in :mod:`.utils`.
"""

from .utils import prompt, prompt_bool, prompt_choice, prompt_select

__all__ = ["prompt", "prompt_bool", "prompt_choice", "prompt_select"]
