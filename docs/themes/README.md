# Theme Gallery for Docx2Shelf

This directory contains a collection of custom themes and style examples for creating beautiful EPUBs. Each theme is designed for specific genres, platforms, or aesthetic preferences.

## Built-in Themes

Docx2Shelf includes three built-in themes that can be used with the `--theme` parameter:

### Serif Theme (Default)
**Best for:** Fiction, literature, traditional books
```bash
docx2shelf build --theme serif manuscript.docx
```

**Characteristics:**
- Traditional serif font (Georgia, Times New Roman)
- Classic book typography
- Comfortable reading experience
- Good for long-form content

### Sans Theme
**Best for:** Non-fiction, technical documentation, modern books
```bash
docx2shelf build --theme sans manuscript.docx
```

**Characteristics:**
- Clean sans-serif fonts (Arial, Helvetica)
- Modern, minimalist appearance
- Good for screens and mobile devices
- Clear hierarchy and spacing

### Printlike Theme
**Best for:** Academic texts, formal documents, print reproduction
```bash
docx2shelf build --theme printlike manuscript.docx
```

**Characteristics:**
- Print-ready formatting
- Formal typography
- Page numbers and print conventions
- Academic citation styles

## Custom Theme Gallery

The following custom themes demonstrate different approaches to EPUB styling. You can use these as starting points for your own designs.

### Fiction Themes

#### 1. Romance Novel Theme
**File:** `gallery/romance.css`
**Features:**
- Elegant script fonts for chapter titles
- Soft color palette
- Decorative scene breaks
- Romantic aesthetic

```bash
docx2shelf build --css docs/themes/gallery/romance.css manuscript.docx
```

#### 2. Mystery/Thriller Theme
**File:** `gallery/mystery.css`
**Features:**
- Bold, dramatic typography
- Dark color scheme
- Sharp contrasts
- Suspenseful atmosphere

#### 3. Fantasy/Sci-Fi Theme
**File:** `gallery/fantasy.css`
**Features:**
- Unique fonts for otherworldly feel
- Custom decorative elements
- Rich color palette
- Immersive styling

### Non-Fiction Themes

#### 4. Technical Manual Theme
**File:** `gallery/technical.css`
**Features:**
- Monospace code blocks
- Clear hierarchy
- Professional appearance
- Code syntax highlighting

#### 5. Academic Thesis Theme
**File:** `gallery/academic.css`
**Features:**
- Formal typography
- Citation formatting
- Clear section breaks
- Professional layout

#### 6. Business Book Theme
**File:** `gallery/business.css`
**Features:**
- Corporate styling
- Clean, professional look
- Emphasis on readability
- Chart and graph support

### Specialized Themes

#### 7. Children's Book Theme
**File:** `gallery/childrens.css`
**Features:**
- Large, friendly fonts
- Bright colors
- Fun decorative elements
- High contrast for readability

#### 8. Poetry Collection Theme
**File:** `gallery/poetry.css`
**Features:**
- Elegant typography
- Proper verse formatting
- Artistic layout
- Emphasis on white space

#### 9. Cookbook Theme
**File:** `gallery/cookbook.css`
**Features:**
- Recipe formatting
- Ingredient lists
- Step-by-step instructions
- Food photography optimization

## Platform-Specific Themes

### Amazon KDP Optimized
**File:** `gallery/kdp-optimized.css`
**Features:**
- Kindle-friendly formatting
- Conservative styling
- Maximum compatibility
- KDP guidelines compliance

### Apple Books Enhanced
**File:** `gallery/apple-enhanced.css`
**Features:**
- Advanced typography features
- Custom fonts
- Rich media support
- iOS-optimized styling

### Kobo Premium
**File:** `gallery/kobo-premium.css`
**Features:**
- Kobo-specific optimizations
- Night mode friendly
- Accessibility enhanced
- Multi-language support

## Using Custom Themes

### Basic Usage
```bash
# Use a single custom theme
docx2shelf build --css docs/themes/gallery/romance.css manuscript.docx

# Combine with built-in theme
docx2shelf build --theme serif --css docs/themes/gallery/enhancements.css manuscript.docx
```

### Advanced Customization
```bash
# Multiple CSS files
docx2shelf build \
  --theme sans \
  --css docs/themes/gallery/base.css \
  --css docs/themes/gallery/custom.css \
  manuscript.docx
```

### Theme Development
```bash
# Use inspection mode for theme development
docx2shelf build \
  --css your-theme.css \
  --inspect \
  --preview \
  manuscript.docx
```

## Theme Development Guide

### CSS Structure

Each theme should follow this structure:

```css
/* Theme Name: [Theme Name]
 * Description: [Brief description]
 * Best for: [Target use cases]
 * Author: [Your name]
 * Version: [Version number]
 */

/* Typography */
body {
    font-family: [primary font stack];
    font-size: [base size];
    line-height: [line height];
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-family: [heading font stack];
    /* heading styles */
}

/* Paragraphs */
p {
    /* paragraph styles */
}

/* Special Elements */
.chapter-title {
    /* chapter title styles */
}

.scene-break {
    /* scene break styles */
}

/* Platform-specific adjustments */
@media screen and (max-width: 600px) {
    /* Mobile optimizations */
}
```

### Font Guidelines

**Safe Font Stacks:**
```css
/* Serif options */
font-family: Georgia, "Times New Roman", Times, serif;
font-family: "Crimson Text", Georgia, serif;
font-family: "Libre Baskerville", Georgia, serif;

/* Sans-serif options */
font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
font-family: "Open Sans", Arial, sans-serif;
font-family: "Lato", "Helvetica Neue", sans-serif;

/* Monospace options */
font-family: "Courier New", Courier, monospace;
font-family: "Source Code Pro", monospace;
```

### Color Guidelines

**High Contrast (Accessibility):**
```css
/* Light theme */
body { background: #ffffff; color: #000000; }

/* Dark theme */
body { background: #1a1a1a; color: #e6e6e6; }

/* High contrast */
body { background: #000000; color: #ffffff; }
```

**Reading-Friendly Colors:**
```css
/* Warm reading */
body { background: #fdf6e3; color: #586e75; }

/* Cool reading */
body { background: #f8f8f2; color: #44475a; }

/* Sepia tone */
body { background: #f4ecd8; color: #5c4b37; }
```

### Responsive Design

```css
/* Base styles for larger screens */
body {
    font-size: 16px;
    margin: 2em;
}

/* Tablet adjustments */
@media screen and (max-width: 768px) {
    body {
        font-size: 15px;
        margin: 1.5em;
    }
}

/* Mobile adjustments */
@media screen and (max-width: 480px) {
    body {
        font-size: 14px;
        margin: 1em;
    }

    h1 {
        font-size: 1.5em;
    }
}
```

## Theme Testing Checklist

### Visual Testing
- [ ] Test on different screen sizes
- [ ] Check font rendering on various devices
- [ ] Verify color contrast and readability
- [ ] Test dark mode compatibility (if applicable)

### Platform Testing
- [ ] Amazon Kindle apps
- [ ] Apple Books
- [ ] Kobo readers
- [ ] Google Play Books
- [ ] Adobe Digital Editions

### Accessibility Testing
- [ ] Color contrast ratio (4.5:1 minimum)
- [ ] Font size scalability
- [ ] Screen reader compatibility
- [ ] Keyboard navigation

### Performance Testing
- [ ] CSS file size optimization
- [ ] Font loading performance
- [ ] Image optimization
- [ ] Load time on slower devices

## Contributing Themes

We welcome contributions of new themes! To contribute:

1. **Create Your Theme**
   - Follow the CSS structure guidelines
   - Include comprehensive comments
   - Test across multiple platforms

2. **Documentation**
   - Add description and use cases
   - Include screenshots (if possible)
   - Provide usage examples

3. **Submit**
   - Create a pull request
   - Include test files if needed
   - Update this README

### Theme Submission Template

```css
/*
 * Theme Name: [Your Theme Name]
 * Description: [Detailed description of the theme]
 * Best for: [Target genres/use cases]
 * Platforms tested: [List of tested platforms]
 * Author: [Your name]
 * License: [License, typically MIT]
 * Version: 1.0.0
 */
```

## Troubleshooting Themes

### Common Issues

**Fonts Not Loading:**
- Use web-safe font stacks
- Include fallback fonts
- Test font availability across platforms

**Layout Breaking on Mobile:**
- Use relative units (em, rem, %)
- Include responsive CSS rules
- Test on various screen sizes

**Colors Not Displaying:**
- Use web-safe color formats
- Test in different reader apps
- Consider accessibility requirements

**Performance Issues:**
- Minimize CSS file size
- Optimize font loading
- Avoid complex animations

### Debug Mode

Use inspection mode to debug theme issues:

```bash
docx2shelf build \
  --css your-theme.css \
  --inspect \
  --dry-run \
  manuscript.docx
```

This creates a `.src/` folder with the generated CSS that you can examine and modify.

## Resources

### Typography Resources
- [Google Fonts](https://fonts.google.com/) - Free web fonts
- [Font Squirrel](https://www.fontsquirrel.com/) - Font resources and tools
- [Practical Typography](https://practicaltypography.com/) - Typography guide

### Color Tools
- [Contrast Checker](https://webaim.org/resources/contrastchecker/) - Accessibility testing
- [Coolors](https://coolors.co/) - Color palette generator
- [Color Hunt](https://colorhunt.co/) - Color palette inspiration

### CSS Resources
- [MDN CSS Reference](https://developer.mozilla.org/en-US/docs/Web/CSS) - Comprehensive CSS documentation
- [Can I Use](https://caniuse.com/) - CSS feature compatibility
- [CSS-Tricks](https://css-tricks.com/) - CSS tips and techniques

Happy theming! Create beautiful, readable EPUBs that readers will love.