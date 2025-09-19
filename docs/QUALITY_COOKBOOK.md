# Quality Cookbook for Docx2Shelf

This guide helps you structure your DOCX documents for optimal EPUB conversion results. Learn best practices, avoid common pitfalls, and see before/after examples to create professional-quality ebooks.

## Table of Contents

1. [Document Structure](#document-structure)
2. [Typography & Formatting](#typography--formatting)
3. [Images & Media](#images--media)
4. [Tables & Lists](#tables--lists)
5. [Styles & Themes](#styles--themes)
6. [Common Pitfalls](#common-pitfalls)
7. [Before/After Examples](#beforeafter-examples)
8. [Platform-Specific Guidelines](#platform-specific-guidelines)

## Document Structure

### ✅ Best Practices

**Use Proper Heading Hierarchy**
```
Heading 1: Chapter titles
Heading 2: Major sections
Heading 3: Subsections
Heading 4+: Minor subsections
```

**Example Structure:**
```
# Chapter 1: Introduction (Heading 1)
## Setting the Scene (Heading 2)
### Character Backgrounds (Heading 3)
#### Main Character (Heading 4)

# Chapter 2: The Journey Begins (Heading 1)
## The Departure (Heading 2)
```

**Benefits:**
- Clean table of contents generation
- Logical chapter splitting
- Better accessibility
- Consistent navigation

### ❌ Common Mistakes

**Manual Formatting Instead of Styles**
```
❌ Bold text that looks like a heading
❌ Centered text with larger font
❌ ALL CAPS FOR EMPHASIS
```

**Inconsistent Heading Levels**
```
❌ Chapter 1 (Heading 1)
❌ Section A (Heading 3) - Skips Heading 2
❌ Chapter 2 (Heading 2) - Inconsistent level
```

### 🔧 How to Fix

1. **Use Word's Built-in Heading Styles**
   - Home tab → Styles → Heading 1, 2, 3, etc.
   - Modify styles to match your preferred appearance

2. **Structure Check**
   - View → Navigation Pane to see document outline
   - Ensure logical hierarchy with no skipped levels

## Typography & Formatting

### ✅ Best Practices

**Character Formatting**
- Use *italic* for emphasis, thoughts, foreign words
- Use **bold** for strong emphasis, keywords
- Use `code` formatting for technical terms
- Use proper quote marks: "smart quotes" not "straight quotes"

**Paragraph Formatting**
- Use styles for consistency (Normal, Quote, etc.)
- Set appropriate line spacing (1.15x or 1.5x)
- Use proper paragraph spacing instead of manual line breaks

**Special Characters**
- Em dashes (—) for breaks in thought
- En dashes (–) for ranges (pages 10–20)
- Ellipsis (…) not three periods (...)
- Proper apostrophes (don't not don't)

### ❌ Common Mistakes

**Manual Formatting**
```
❌ Multiple spaces for indentation
❌ Tab characters for alignment
❌ Manual line breaks for spacing
❌ Using underline for emphasis
```

**Inconsistent Formatting**
```
❌ Mixing italic and bold for the same purpose
❌ Inconsistent quote mark styles
❌ Random font changes throughout document
```

### 🔧 How to Fix

1. **Clean Up Manual Formatting**
   - Find & Replace to remove extra spaces/tabs
   - Use Styles for consistent formatting
   - Replace straight quotes with smart quotes

2. **Character Formatting Standards**
   ```
   Thoughts: "She wondered, What am I doing here?"
   Emphasis: This is *really* important.
   Strong: **Never** do this.
   Technical: Use the `docx2shelf` command.
   ```

## Images & Media

### ✅ Best Practices

**Image Quality**
- Use high-resolution images (300 DPI minimum)
- Prefer PNG for graphics, JPEG for photos
- Ensure images are properly embedded, not linked

**Image Placement**
- Use "In Line with Text" wrapping
- Add descriptive captions
- Include alt text for accessibility

**File Organization**
- Keep images in same folder as DOCX
- Use descriptive filenames
- Optimize file sizes before insertion

### ❌ Common Mistakes

**Poor Image Handling**
```
❌ Low-resolution images (pixelated in EPUB)
❌ Linked images instead of embedded
❌ Images with tight text wrapping
❌ Missing alt text
```

**File Issues**
```
❌ Huge image files (slowing conversion)
❌ Exotic image formats
❌ Images in separate folders
```

### 🔧 How to Fix

1. **Image Optimization**
   - Resize images to appropriate dimensions
   - Compress large files
   - Convert to web-friendly formats

2. **Proper Insertion**
   - Insert → Pictures → This Device
   - Right-click → Format Picture → Layout → In Line with Text
   - Add meaningful alt text via Picture Format → Alt Text

## Tables & Lists

### ✅ Best Practices

**Table Design**
- Use proper table headers
- Keep tables simple and readable
- Avoid merged cells when possible
- Use consistent formatting

**List Formatting**
- Use built-in bullet/numbered lists
- Maintain consistent indentation
- Use appropriate list types

### ❌ Common Mistakes

**Table Problems**
```
❌ Complex merged cell layouts
❌ Tables used for page layout
❌ Missing table headers
❌ Inconsistent table formatting
```

**List Issues**
```
❌ Manual bullets using asterisks or dashes
❌ Inconsistent indentation
❌ Mixing list types randomly
```

### 🔧 How to Fix

1. **Table Simplification**
   - Break complex tables into multiple simple ones
   - Use clear headers
   - Ensure tables are readable on small screens

2. **List Cleanup**
   - Convert manual lists to proper Word lists
   - Use Home → Bullets or Numbering
   - Maintain consistent styling

## Styles & Themes

### ✅ Best Practices

**Style Usage**
- Define and use paragraph styles consistently
- Create character styles for special formatting
- Use built-in styles when possible

**Theme Selection**
```bash
# Available themes in docx2shelf
--theme serif      # Traditional book appearance
--theme sans       # Modern, clean look
--theme printlike  # Print-ready formatting
```

**Custom Styling**
- Create custom CSS files for unique looks
- Use CSS variables for easy theme modification
- Test across different reading devices

### 🔧 Style Examples

**Fiction Book Styles**
```css
/* Custom fiction styling */
.dialogue {
    margin-left: 2em;
    font-style: italic;
}

.scene-break {
    text-align: center;
    margin: 2em 0;
    font-size: 1.2em;
}
```

**Non-Fiction Styles**
```css
/* Technical documentation styling */
.code-block {
    background: #f5f5f5;
    border-left: 4px solid #007acc;
    padding: 1em;
    font-family: monospace;
}

.tip-box {
    background: #e8f4fd;
    border: 1px solid #bee5eb;
    padding: 1em;
    margin: 1em 0;
}
```

## Common Pitfalls

### 1. Inconsistent Formatting

**Problem:** Mixed formatting throughout the document
```
Chapter titles sometimes bold, sometimes italic
Inconsistent paragraph spacing
Random font changes
```

**Solution:** Use Word styles consistently
```
1. Define styles for each element type
2. Apply styles throughout document
3. Use Find & Replace to fix inconsistencies
```

### 2. Poor Image Handling

**Problem:** Images don't display properly in EPUB
```
❌ Linked images that break
❌ Oversized images that slow loading
❌ Images with complex wrapping
```

**Solution:** Proper image embedding
```
1. Insert images using Insert → Pictures
2. Set wrapping to "In Line with Text"
3. Optimize image sizes before insertion
4. Add descriptive alt text
```

### 3. Manual Layout Attempts

**Problem:** Trying to control exact positioning
```
❌ Multiple line breaks for spacing
❌ Spaces and tabs for alignment
❌ Manual page breaks everywhere
```

**Solution:** Let EPUB handle layout
```
1. Use proper paragraph spacing
2. Use styles for consistent formatting
3. Minimize manual page breaks
4. Focus on content structure, not appearance
```

### 4. Complex Table Layouts

**Problem:** Tables that don't work on mobile
```
❌ Wide tables with many columns
❌ Complex merged cell layouts
❌ Tables used for page design
```

**Solution:** Simplify table design
```
1. Keep tables narrow (3-4 columns max)
2. Avoid complex merging
3. Use clear headers
4. Consider breaking into multiple tables
```

## Before/After Examples

### Example 1: Chapter Structure

**❌ Before (Poor Structure)**
```
CHAPTER ONE: THE BEGINNING

This is the first chapter of the book. It starts with some
introductory text.


SECTION A: BACKGROUND INFO

Here's some background information that's important to know.


SECTION B: MORE DETAILS

Additional details that flesh out the story.
```

**✅ After (Proper Structure)**
```
# Chapter 1: The Beginning

This is the first chapter of the book. It starts with some introductory text.

## Background Information

Here's some background information that's important to know.

## Additional Details

More details that flesh out the story.
```

**Improvements:**
- Uses proper heading styles (Heading 1, Heading 2)
- Consistent formatting
- Better accessibility
- Clean table of contents generation

### Example 2: Character Formatting

**❌ Before (Manual Formatting)**
```
She thought to herself, "What am I doing here?" The question
echoed in her mind as she walked down the dark hallway.

The sign read: AUTHORIZED PERSONNEL ONLY

Important: Never leave the door unlocked.
```

**✅ After (Proper Formatting)**
```
She thought to herself, *What am I doing here?* The question
echoed in her mind as she walked down the dark hallway.

The sign read: **Authorized Personnel Only**

*Important:* Never leave the door unlocked.
```

**Improvements:**
- Italics for thoughts
- Bold for emphasis
- Consistent formatting throughout

### Example 3: List Formatting

**❌ Before (Manual Lists)**
```
To prepare for the journey, you'll need:

* A sturdy backpack
* Water bottles (at least 2)
  - Insulated bottles work best
  - Consider electrolyte tablets
* Trail snacks
  - Nuts and dried fruit
  - Energy bars
```

**✅ After (Proper Lists)**
```
To prepare for the journey, you'll need:

• A sturdy backpack
• Water bottles (at least 2)
  ◦ Insulated bottles work best
  ◦ Consider electrolyte tablets
• Trail snacks
  ◦ Nuts and dried fruit
  ◦ Energy bars
```

**Improvements:**
- Uses Word's built-in list formatting
- Consistent bullet styles
- Proper indentation hierarchy

## Platform-Specific Guidelines

### Amazon KDP (Kindle)

**Formatting Requirements:**
- Simple, clean formatting works best
- Avoid complex layouts
- Test with Kindle Previewer

**Best Practices:**
```bash
# Recommended docx2shelf settings for KDP
docx2shelf build \
  --theme serif \
  --justify on \
  --hyphenate on \
  --cover-scale contain
```

**Metadata Essentials:**
- Clear, compelling description
- Appropriate categories (BISAC codes)
- Competitive pricing research

### Apple Books

**Design Considerations:**
- Supports advanced typography
- Good CSS support
- High-quality images recommended

**Recommended Settings:**
```bash
# Apple Books optimization
docx2shelf build \
  --theme sans \
  --embed-fonts fonts/ \
  --css custom-apple.css
```

**Special Features:**
- Custom fonts work well
- Advanced CSS animations supported
- High-resolution images preferred

### Kobo

**Technical Requirements:**
- EPUB 3 preferred
- Good accessibility support
- Standard CSS works reliably

**Optimization:**
```bash
# Kobo-friendly build
docx2shelf build \
  --theme printlike \
  --page-numbers on \
  --epubcheck
```

**Metadata Focus:**
- Detailed descriptions
- Series information important
- Good categorization

### Draft2Digital (Multi-platform)

**Universal Compatibility:**
- Conservative formatting approach
- Avoid platform-specific features
- Test across multiple readers

**Safe Settings:**
```bash
# Maximum compatibility build
docx2shelf build \
  --theme serif \
  --justify off \
  --hyphenate off \
  --epub-version 2
```

## Quality Checklist

### Pre-Conversion Checklist

- [ ] Document uses proper heading hierarchy
- [ ] All images are embedded, not linked
- [ ] Consistent paragraph and character formatting
- [ ] Tables are simple and mobile-friendly
- [ ] Lists use Word's built-in formatting
- [ ] No manual page breaks except chapter endings
- [ ] Spell check and grammar check completed

### Post-Conversion Checklist

- [ ] EPUB passes EPUBCheck validation
- [ ] Table of contents is complete and accurate
- [ ] Images display correctly at different sizes
- [ ] Text flows well on mobile devices
- [ ] Metadata is complete and accurate
- [ ] Cover image meets platform requirements
- [ ] Test reading experience on multiple devices

### Quality Validation Commands

```bash
# Comprehensive quality check
docx2shelf build manuscript.docx \
  --title "Book Title" \
  --author "Author Name" \
  --cover cover.jpg \
  --dry-run \
  --inspect

# Validation and preview
docx2shelf build manuscript.docx \
  --title "Book Title" \
  --author "Author Name" \
  --cover cover.jpg \
  --preview

# Platform-specific validation
docx2shelf checklist --epub output.epub --store kdp
```

## Troubleshooting Common Issues

### Issue: Images Don't Appear

**Symptoms:** Black boxes or missing images in EPUB

**Solutions:**
1. Check image embedding: Insert → Pictures → This Device
2. Verify image formats (PNG, JPEG preferred)
3. Ensure images are in same folder as DOCX
4. Reduce image file sizes if very large

### Issue: Table of Contents Problems

**Symptoms:** Missing chapters or wrong page numbers

**Solutions:**
1. Use proper heading styles (Heading 1, 2, 3)
2. Check heading hierarchy consistency
3. Update TOC in Word before conversion
4. Verify navigation in EPUB viewer

### Issue: Formatting Inconsistencies

**Symptoms:** Mixed fonts, spacing, or styling

**Solutions:**
1. Use Find & Replace to clean up formatting
2. Apply styles consistently throughout document
3. Remove manual formatting where possible
4. Check character and paragraph styles

### Issue: Poor Mobile Display

**Symptoms:** Text too small or layout broken on phones

**Solutions:**
1. Simplify table designs
2. Use relative font sizes
3. Test on various screen sizes
4. Avoid fixed-width elements

## Getting Help

If you encounter issues not covered in this guide:

1. **Check the Documentation**: Review the main README and help files
2. **Test Systematically**: Isolate the problem in a simple test document
3. **Use Diagnostic Tools**: Run with `--inspect` and `--dry-run` flags
4. **Community Support**: Visit the GitHub Discussions page
5. **Report Bugs**: Use GitHub Issues with sample files (redacted if needed)

## Advanced Tips

### Custom CSS Workflow

1. **Start with a Base Theme**
   ```bash
   docx2shelf build --theme serif --css custom.css
   ```

2. **Iterative Development**
   ```bash
   # Build with inspection for debugging
   docx2shelf build --inspect --preview
   ```

3. **Test Across Platforms**
   - Use different reading apps
   - Test on various screen sizes
   - Validate accessibility

### Batch Processing

For multiple books with similar formatting:

```bash
# Create a profile for your style
docx2shelf build \
  --profile fiction-series \
  --theme custom-fiction \
  --series "My Series Name" \
  manuscript.docx
```

### Automation Integration

```bash
# CI/CD pipeline example
docx2shelf build \
  --no-prompt \
  --auto-install-tools \
  --json \
  manuscript.docx
```

This cookbook should help you create professional-quality EPUBs consistently. Remember: good EPUB conversion starts with well-structured source documents!