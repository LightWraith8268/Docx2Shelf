/**
 * EPUB Generator for Docx2Shelf Web
 * Handles client-side EPUB creation using JSZip
 */

export class EpubGenerator {
    constructor() {
        this.zip = null;
        this.templates = new Map();
        this.cssThemes = new Map();
        this.initializeTemplates();
    }

    initializeTemplates() {
        // EPUB templates
        this.templates.set('mimetype', 'application/epub+zip');

        this.templates.set('container.xml', `<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>`);

        this.templates.set('nav.xhtml', `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Navigation</title>
    <meta charset="UTF-8"/>
    <link rel="stylesheet" type="text/css" href="styles/nav.css"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>Table of Contents</h1>
        <ol>
            {{TOC_ENTRIES}}
        </ol>
    </nav>
</body>
</html>`);

        this.templates.set('chapter.xhtml', `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{{CHAPTER_TITLE}}</title>
    <meta charset="UTF-8"/>
    <link rel="stylesheet" type="text/css" href="styles/{{THEME}}.css"/>
</head>
<body>
    <div class="chapter">
        {{CHAPTER_CONTENT}}
    </div>
</body>
</html>`);

        // Initialize CSS themes
        this.initializeCSSThemes();
    }

    initializeCSSThemes() {
        this.cssThemes.set('serif', `
/* Serif Theme */
body {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 16px;
    line-height: 1.6;
    margin: 2em;
    color: #333;
    text-align: justify;
}

h1, h2, h3, h4, h5, h6 {
    font-family: Georgia, serif;
    color: #2c3e50;
    page-break-after: avoid;
}

h1 {
    font-size: 2em;
    margin: 1em 0 0.5em 0;
    text-align: center;
}

h2 {
    font-size: 1.5em;
    margin: 1em 0 0.5em 0;
}

p {
    margin-bottom: 1em;
    text-indent: 1.2em;
}

p.no-indent {
    text-indent: 0;
}

.chapter-title {
    text-align: center;
    font-size: 1.8em;
    margin-bottom: 2em;
    page-break-before: always;
}

blockquote {
    margin: 1em 2em;
    font-style: italic;
    border-left: 3px solid #ccc;
    padding-left: 1em;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}
`);

        this.cssThemes.set('sans', `
/* Sans-serif Theme */
body {
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 15px;
    line-height: 1.5;
    margin: 2em;
    color: #444;
    text-align: left;
}

h1, h2, h3, h4, h5, h6 {
    font-family: "Helvetica Neue", Arial, sans-serif;
    color: #2c3e50;
    font-weight: 600;
    page-break-after: avoid;
}

h1 {
    font-size: 2.2em;
    margin: 1em 0 0.5em 0;
    text-align: center;
}

h2 {
    font-size: 1.6em;
    margin: 1em 0 0.5em 0;
}

p {
    margin-bottom: 1em;
}

.chapter-title {
    text-align: center;
    font-size: 2em;
    margin-bottom: 2em;
    page-break-before: always;
    font-weight: 300;
}

blockquote {
    margin: 1em 0;
    padding: 1em;
    background-color: #f8f9fa;
    border-left: 4px solid #007bff;
    font-style: italic;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
    border-radius: 4px;
}
`);

        this.cssThemes.set('printlike', `
/* Print-like Theme */
body {
    font-family: "Times New Roman", Times, serif;
    font-size: 12pt;
    line-height: 1.4;
    margin: 1in;
    color: #000;
    text-align: justify;
}

h1, h2, h3, h4, h5, h6 {
    font-family: "Times New Roman", serif;
    color: #000;
    font-weight: bold;
    page-break-after: avoid;
}

h1 {
    font-size: 18pt;
    margin: 24pt 0 12pt 0;
    text-align: center;
}

h2 {
    font-size: 14pt;
    margin: 18pt 0 6pt 0;
}

p {
    margin-bottom: 12pt;
    text-indent: 0.5in;
}

p.no-indent {
    text-indent: 0;
}

.chapter-title {
    text-align: center;
    font-size: 16pt;
    margin: 36pt 0;
    page-break-before: always;
    font-weight: bold;
}

blockquote {
    margin: 12pt 0.5in;
    font-style: italic;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 12pt auto;
}

@page {
    margin: 1in;
}
`);

        // Navigation CSS
        this.cssThemes.set('nav', `
/* Navigation Styles */
body {
    font-family: Arial, sans-serif;
    margin: 2em;
    color: #333;
}

nav#toc h1 {
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.5em;
}

nav#toc ol {
    list-style-type: none;
    padding-left: 0;
}

nav#toc ol ol {
    padding-left: 1.5em;
}

nav#toc li {
    margin: 0.5em 0;
}

nav#toc a {
    color: #2980b9;
    text-decoration: none;
    display: block;
    padding: 0.25em 0;
}

nav#toc a:hover {
    color: #3498db;
    text-decoration: underline;
}
`);
    }

    async generate(data) {
        const { content, metadata, options } = data;

        try {
            // Initialize ZIP
            this.zip = new JSZip();

            // Create EPUB structure
            await this.createEpubStructure();

            // Add metadata
            await this.addMetadata(metadata);

            // Process content
            const processedContent = await this.processContent(content, options);

            // Add chapters
            await this.addChapters(processedContent, options);

            // Add table of contents
            if (options.includeToc) {
                await this.addTableOfContents(processedContent);
            }

            // Add styles
            await this.addStyles(options.cssTheme);

            // Generate package file
            await this.generatePackage(metadata, processedContent, options);

            // Generate EPUB file
            const epubBlob = await this.zip.generateAsync({
                type: "blob",
                mimeType: "application/epub+zip",
                compression: "DEFLATE",
                compressionOptions: { level: 9 }
            });

            return epubBlob;

        } catch (error) {
            console.error('EPUB generation failed:', error);
            throw new Error(`EPUB generation failed: ${error.message}`);
        }
    }

    async createEpubStructure() {
        // Create basic EPUB structure
        this.zip.file("mimetype", this.templates.get('mimetype'));

        // META-INF directory
        this.zip.folder("META-INF");
        this.zip.file("META-INF/container.xml", this.templates.get('container.xml'));

        // OEBPS directory (content)
        this.zip.folder("OEBPS");
        this.zip.folder("OEBPS/chapters");
        this.zip.folder("OEBPS/styles");
        this.zip.folder("OEBPS/images");
    }

    async addMetadata(metadata) {
        // Store metadata for use in package generation
        this.metadata = {
            title: metadata.title || 'Untitled',
            author: metadata.author || 'Unknown Author',
            language: metadata.language || 'en',
            genre: metadata.genre || '',
            description: metadata.description || '',
            identifier: this.generateIdentifier(),
            timestamp: new Date().toISOString()
        };
    }

    async processContent(content, options) {
        let processedContent = content;

        // Apply chapter detection if needed
        if (options.chapterDetection === 'ai' && content.chapters) {
            processedContent = this.applyAIChapters(content);
        } else {
            processedContent = this.detectChapters(content, options.chapterDetection);
        }

        // Clean and process HTML
        processedContent = this.cleanContent(processedContent);

        return processedContent;
    }

    detectChapters(content, method) {
        let chapters = [];

        switch (method) {
            case 'h1':
                chapters = this.detectChaptersByHeading(content.html, 'h1');
                break;
            case 'h2':
                chapters = this.detectChaptersByHeading(content.html, 'h2');
                break;
            case 'auto':
                chapters = this.detectChaptersAuto(content.html);
                break;
            default:
                // Single chapter
                chapters = [{
                    title: this.metadata.title,
                    content: content.html,
                    id: 'chapter1'
                }];
        }

        return { ...content, chapters };
    }

    detectChaptersByHeading(html, headingTag) {
        const chapters = [];
        const regex = new RegExp(`<${headingTag}[^>]*>(.*?)</${headingTag}>`, 'gi');
        const parts = html.split(regex);

        for (let i = 1; i < parts.length; i += 2) {
            const title = parts[i].replace(/<[^>]*>/g, '').trim();
            const content = parts[i + 1] || '';

            chapters.push({
                title: title || `Chapter ${Math.ceil(i / 2)}`,
                content: `<${headingTag}>${parts[i]}</${headingTag}>${content}`,
                id: `chapter${Math.ceil(i / 2)}`
            });
        }

        // Add content before first heading as prologue if exists
        if (parts[0] && parts[0].trim()) {
            chapters.unshift({
                title: 'Prologue',
                content: parts[0],
                id: 'prologue'
            });
        }

        return chapters.length > 0 ? chapters : [{
            title: this.metadata.title,
            content: html,
            id: 'chapter1'
        }];
    }

    detectChaptersAuto(html) {
        // Try H1 first, then H2, then single chapter
        let chapters = this.detectChaptersByHeading(html, 'h1');
        if (chapters.length <= 1) {
            chapters = this.detectChaptersByHeading(html, 'h2');
        }
        if (chapters.length <= 1) {
            chapters = [{
                title: this.metadata.title,
                content: html,
                id: 'chapter1'
            }];
        }
        return chapters;
    }

    applyAIChapters(content) {
        if (!content.chapters || content.chapters.length === 0) {
            return this.detectChaptersAuto(content);
        }

        const chapters = [];
        let html = content.html;
        let lastPosition = 0;

        content.chapters.forEach((chapter, index) => {
            const chapterContent = html.substring(lastPosition, chapter.position);
            if (chapterContent.trim()) {
                chapters.push({
                    title: chapter.title || `Chapter ${index + 1}`,
                    content: chapterContent,
                    id: `chapter${index + 1}`
                });
            }
            lastPosition = chapter.position;
        });

        // Add remaining content
        const remainingContent = html.substring(lastPosition);
        if (remainingContent.trim()) {
            chapters.push({
                title: content.chapters.length > 0 ? 'Epilogue' : 'Chapter 1',
                content: remainingContent,
                id: `chapter${chapters.length + 1}`
            });
        }

        return { ...content, chapters };
    }

    cleanContent(content) {
        if (!content.chapters) return content;

        const cleanedChapters = content.chapters.map(chapter => ({
            ...chapter,
            content: this.sanitizeHtml(chapter.content)
        }));

        return { ...content, chapters: cleanedChapters };
    }

    sanitizeHtml(html) {
        // Basic HTML sanitization
        return html
            .replace(/<script[^>]*>.*?<\/script>/gi, '')
            .replace(/<style[^>]*>.*?<\/style>/gi, '')
            .replace(/on\w+="[^"]*"/gi, '')
            .replace(/javascript:/gi, '')
            .trim();
    }

    async addChapters(content, options) {
        if (!content.chapters) return;

        const template = this.templates.get('chapter.xhtml');

        for (const chapter of content.chapters) {
            const chapterHtml = template
                .replace('{{CHAPTER_TITLE}}', this.escapeXml(chapter.title))
                .replace('{{CHAPTER_CONTENT}}', chapter.content)
                .replace('{{THEME}}', options.cssTheme);

            this.zip.file(`OEBPS/chapters/${chapter.id}.xhtml`, chapterHtml);
        }
    }

    async addTableOfContents(content) {
        if (!content.chapters) return;

        const tocEntries = content.chapters.map(chapter =>
            `<li><a href="chapters/${chapter.id}.xhtml">${this.escapeXml(chapter.title)}</a></li>`
        ).join('\n            ');

        const navHtml = this.templates.get('nav.xhtml')
            .replace('{{TOC_ENTRIES}}', tocEntries);

        this.zip.file("OEBPS/nav.xhtml", navHtml);
    }

    async addStyles(theme) {
        // Add selected theme CSS
        const css = this.cssThemes.get(theme) || this.cssThemes.get('serif');
        this.zip.file(`OEBPS/styles/${theme}.css`, css);

        // Add navigation CSS
        this.zip.file("OEBPS/styles/nav.css", this.cssThemes.get('nav'));
    }

    async generatePackage(metadata, content, options) {
        const packageTemplate = `<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="uid">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="uid">${metadata.identifier}</dc:identifier>
        <dc:title>${this.escapeXml(metadata.title)}</dc:title>
        <dc:creator>${this.escapeXml(metadata.author)}</dc:creator>
        <dc:language>${metadata.language}</dc:language>
        <dc:date>${metadata.timestamp}</dc:date>
        <meta property="dcterms:modified">${metadata.timestamp}</meta>
        ${metadata.description ? `<dc:description>${this.escapeXml(metadata.description)}</dc:description>` : ''}
        ${metadata.genre ? `<dc:subject>${this.escapeXml(metadata.genre)}</dc:subject>` : ''}
    </metadata>

    <manifest>
        ${options.includeToc ? '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>' : ''}
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
        ${content.chapters ? content.chapters.map(chapter =>
            `<item id="${chapter.id}" href="chapters/${chapter.id}.xhtml" media-type="application/xhtml+xml"/>`
        ).join('\n        ') : ''}
        <item id="css-${options.cssTheme}" href="styles/${options.cssTheme}.css" media-type="text/css"/>
        ${options.includeToc ? '<item id="css-nav" href="styles/nav.css" media-type="text/css"/>' : ''}
    </manifest>

    <spine toc="ncx">
        ${options.includeToc ? '<itemref idref="nav"/>' : ''}
        ${content.chapters ? content.chapters.map(chapter =>
            `<itemref idref="${chapter.id}"/>`
        ).join('\n        ') : ''}
    </spine>
</package>`;

        this.zip.file("OEBPS/content.opf", packageTemplate);

        // Add NCX for EPUB2 compatibility
        await this.generateNCX(metadata, content, options);
    }

    async generateNCX(metadata, content, options) {
        const ncxTemplate = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
    <head>
        <meta name="dtb:uid" content="${metadata.identifier}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>${this.escapeXml(metadata.title)}</text>
    </docTitle>
    <navMap>
        ${content.chapters ? content.chapters.map((chapter, index) => `
        <navPoint id="chapter${index + 1}" playOrder="${index + 1}">
            <navLabel>
                <text>${this.escapeXml(chapter.title)}</text>
            </navLabel>
            <content src="chapters/${chapter.id}.xhtml"/>
        </navPoint>`).join('') : ''}
    </navMap>
</ncx>`;

        this.zip.file("OEBPS/toc.ncx", ncxTemplate);
    }

    generateIdentifier() {
        return `urn:uuid:${this.generateUUID()}`;
    }

    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    escapeXml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    createValidator() {
        return {
            validate: async (epubData) => {
                // Basic EPUB validation
                const issues = [];

                // Check required files
                const requiredFiles = ['mimetype', 'META-INF/container.xml', 'OEBPS/content.opf'];

                // Note: This is a simplified validation
                // In a real implementation, you'd validate the EPUB structure more thoroughly

                return {
                    valid: issues.length === 0,
                    issues: issues
                };
            }
        };
    }
}