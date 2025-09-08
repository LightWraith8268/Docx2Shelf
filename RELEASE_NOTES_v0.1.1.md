# Docx2Shelf 0.1.1

Bug fixes and user-defined chapter starts feature for enhanced TOC control.

## New Features
- **User-Defined Chapter Starts**: New `--chapter-start-mode` and `--chapter-starts` parameters allow manual TOC chapter definition
- **Flexible TOC Modes**: Choose between auto (scan headings), manual (user-defined patterns), or mixed modes
- **Pattern Matching**: Support for both exact text matches and regex patterns to find chapter starts in content
- **Interactive Chapter Setup**: CLI prompts for chapter mode selection and pattern entry during guided flow
- **Metadata File Integration**: Add `Chapter-Start-Mode` and `Chapter-Starts` fields to metadata.txt templates

## Improvements  
- Enhanced metadata summary display shows current chapter detection mode
- Better fallback handling when user-defined patterns aren't found in content
- Improved TOC generation preserves existing heading structure in auto mode

## Usage
```bash
# Manual chapter definition via CLI
docx2shelf build --docx book.docx --chapter-start-mode manual --chapter-starts "Prologue,Chapter 1,Epilogue"

# Via metadata.txt
Chapter-Start-Mode: manual
Chapter-Starts: Prologue, Chapter 1, Epilogue
```

## Bug Fixes
- Fixed import organization and code formatting issues

This release addresses the need for better TOC control when automatic heading scanning is insufficient or disabled, giving users full control over chapter organization in their EPUB navigation.