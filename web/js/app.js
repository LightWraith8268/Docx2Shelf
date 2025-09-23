/**
 * Docx2Shelf Web Application
 * Main application controller and initialization
 */

import { FileHandler } from './file-handler.js';
import { EpubGenerator } from './epub-generator.js';
import { SettingsManager } from './settings-manager.js';
import { UIManager } from './ui-manager.js';
import { AIChapterDetection } from './ai/chapter-detection.js';
import { WebLLMClient } from './ai/web-llm-client.js';

class Docx2ShelfWeb {
    constructor() {
        this.fileHandler = new FileHandler();
        this.epubGenerator = new EpubGenerator();
        this.settingsManager = new SettingsManager();
        this.uiManager = new UIManager();
        this.aiDetection = new AIChapterDetection();
        this.webLLM = new WebLLMClient();

        this.currentFile = null;
        this.conversionState = {
            isConverting: false,
            progress: 0,
            status: 'idle'
        };

        this.initialize();
    }

    async initialize() {
        console.log('Initializing Docx2Shelf Web...');

        // Load settings
        await this.settingsManager.load();

        // Initialize UI
        this.uiManager.initialize();

        // Apply saved theme
        this.applyTheme(this.settingsManager.get('ui.theme', 'light'));

        // Setup event listeners
        this.setupEventListeners();

        // Initialize AI if enabled
        if (this.settingsManager.get('ai.enabled', true)) {
            await this.initializeAI();
        }

        console.log('Docx2Shelf Web initialized successfully');
    }

    setupEventListeners() {
        // File input
        const fileInput = document.getElementById('file-input');
        const browseBtn = document.getElementById('browse-btn');
        const uploadArea = document.getElementById('upload-area');
        const clearFileBtn = document.getElementById('clear-file');

        browseBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));
        clearFileBtn.addEventListener('click', () => this.clearFile());

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            if (file) this.handleFileSelect(file);
        });

        // Tab navigation
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Conversion
        const convertBtn = document.getElementById('convert-btn');
        convertBtn.addEventListener('click', () => this.startConversion());

        // AI service selection
        document.querySelectorAll('input[name="ai-service"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.handleAIServiceChange(e.target.value));
        });

        // Test AI
        const testAIBtn = document.getElementById('test-ai');
        testAIBtn.addEventListener('click', () => this.testAIConfiguration());

        // Settings
        const settingsBtn = document.getElementById('settings-btn');
        settingsBtn.addEventListener('click', () => this.openSettings());

        // Form inputs
        this.setupFormListeners();

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    setupFormListeners() {
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('change', () => this.validateForm());
            input.addEventListener('input', () => this.validateForm());
        });

        // Auto-fill suggestions
        const titleInput = document.getElementById('book-title');
        const authorInput = document.getElementById('book-author');

        titleInput.addEventListener('blur', () => this.suggestMetadata());
    }

    async handleFileSelect(file) {
        if (!file) return;

        try {
            this.uiManager.showLoading('Reading file...');

            // Validate file type
            const supportedTypes = [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/html',
                'text/markdown',
                'text/plain'
            ];

            const fileExtension = file.name.split('.').pop().toLowerCase();
            const supportedExtensions = ['docx', 'html', 'htm', 'md', 'txt'];

            if (!supportedExtensions.includes(fileExtension)) {
                throw new Error(`Unsupported file type: .${fileExtension}`);
            }

            // Read file
            const fileData = await this.fileHandler.readFile(file);

            this.currentFile = {
                name: file.name,
                size: file.size,
                type: fileExtension,
                data: fileData,
                originalFile: file
            };

            // Update UI
            this.displayFileInfo();
            this.validateForm();

            // Auto-suggest metadata from filename
            this.suggestMetadataFromFilename();

            this.uiManager.hideLoading();

        } catch (error) {
            console.error('Error reading file:', error);
            this.uiManager.showError(`Failed to read file: ${error.message}`);
            this.uiManager.hideLoading();
        }
    }

    displayFileInfo() {
        if (!this.currentFile) return;

        const fileInfo = document.getElementById('file-info');
        const fileName = fileInfo.querySelector('.file-name');
        const fileSize = fileInfo.querySelector('.file-size');
        const fileType = fileInfo.querySelector('.file-type');

        fileName.textContent = this.currentFile.name;
        fileSize.textContent = this.formatFileSize(this.currentFile.size);
        fileType.textContent = this.currentFile.type.toUpperCase();

        fileInfo.classList.remove('hidden');
        document.getElementById('upload-area').classList.add('has-file');
    }

    clearFile() {
        this.currentFile = null;
        document.getElementById('file-info').classList.add('hidden');
        document.getElementById('upload-area').classList.remove('has-file');
        document.getElementById('file-input').value = '';
        this.validateForm();
    }

    suggestMetadataFromFilename() {
        if (!this.currentFile) return;

        const filename = this.currentFile.name.replace(/\.[^/.]+$/, ''); // Remove extension

        // Suggest title from filename
        const titleInput = document.getElementById('book-title');
        if (!titleInput.value) {
            // Clean up filename for title
            const suggestedTitle = filename
                .replace(/[-_]/g, ' ')
                .replace(/\b\w/g, l => l.toUpperCase());
            titleInput.value = suggestedTitle;
        }
    }

    async suggestMetadata() {
        // Use AI to suggest metadata based on content
        if (!this.currentFile || !this.settingsManager.get('ai.enabled', true)) return;

        try {
            const content = this.currentFile.data;
            const suggestions = await this.aiDetection.suggestMetadata(content);

            if (suggestions.genre && !document.getElementById('book-genre').value) {
                document.getElementById('book-genre').value = suggestions.genre;
            }

            if (suggestions.description && !document.getElementById('book-description').value) {
                document.getElementById('book-description').value = suggestions.description;
            }

        } catch (error) {
            console.warn('Failed to get AI metadata suggestions:', error);
        }
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
    }

    validateForm() {
        const title = document.getElementById('book-title').value.trim();
        const author = document.getElementById('book-author').value.trim();
        const hasFile = !!this.currentFile;

        const isValid = title && author && hasFile;

        const convertBtn = document.getElementById('convert-btn');
        convertBtn.disabled = !isValid;

        return isValid;
    }

    async startConversion() {
        if (!this.validateForm() || this.conversionState.isConverting) return;

        try {
            this.conversionState.isConverting = true;
            this.updateConversionProgress(0, 'Starting conversion...');

            // Collect form data
            const metadata = this.collectMetadata();
            const options = this.collectConversionOptions();

            // Show progress section
            document.getElementById('conversion-progress').classList.remove('hidden');

            // Start conversion
            await this.performConversion(metadata, options);

        } catch (error) {
            console.error('Conversion failed:', error);
            this.uiManager.showError(`Conversion failed: ${error.message}`);
        } finally {
            this.conversionState.isConverting = false;
        }
    }

    async performConversion(metadata, options) {
        // Step 1: Parse document
        this.updateConversionProgress(10, 'Parsing document...');
        const parsedContent = await this.parseDocument();

        // Step 2: AI chapter detection (if enabled)
        if (options.chapterDetection === 'ai') {
            this.updateConversionProgress(25, 'Detecting chapters with AI...');
            const chapters = await this.aiDetection.detectChapters(parsedContent);
            parsedContent.chapters = chapters;
        }

        // Step 3: Generate EPUB structure
        this.updateConversionProgress(50, 'Generating EPUB structure...');
        const epubData = await this.epubGenerator.generate({
            content: parsedContent,
            metadata: metadata,
            options: options
        });

        // Step 4: Validate EPUB (if enabled)
        if (options.validateEpub) {
            this.updateConversionProgress(80, 'Validating EPUB...');
            await this.validateEpub(epubData);
        }

        // Step 5: Prepare download
        this.updateConversionProgress(100, 'Preparing download...');
        await this.prepareDownload(epubData, metadata.title);

        this.updateConversionProgress(100, 'Conversion complete!');
        this.showDownloadButton();
    }

    async parseDocument() {
        const { data, type } = this.currentFile;

        switch (type) {
            case 'docx':
                return await this.fileHandler.parseDocx(data);
            case 'html':
            case 'htm':
                return await this.fileHandler.parseHtml(data);
            case 'md':
                return await this.fileHandler.parseMarkdown(data);
            case 'txt':
                return await this.fileHandler.parseText(data);
            default:
                throw new Error(`Unsupported file type: ${type}`);
        }
    }

    collectMetadata() {
        return {
            title: document.getElementById('book-title').value.trim(),
            author: document.getElementById('book-author').value.trim(),
            language: document.getElementById('book-language').value,
            genre: document.getElementById('book-genre').value.trim(),
            description: document.getElementById('book-description').value.trim(),
        };
    }

    collectConversionOptions() {
        return {
            cssTheme: document.getElementById('css-theme').value,
            chapterDetection: document.getElementById('chapter-detection').value,
            includeToc: document.getElementById('include-toc').checked,
            validateEpub: document.getElementById('validate-epub').checked,
        };
    }

    updateConversionProgress(percentage, status) {
        const progressFill = document.getElementById('progress-fill');
        const progressPercentage = document.getElementById('progress-percentage');
        const progressStatus = document.getElementById('progress-status');
        const progressLog = document.getElementById('progress-log');

        progressFill.style.width = `${percentage}%`;
        progressPercentage.textContent = `${percentage}%`;
        progressStatus.textContent = status;

        // Add to log
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.textContent = `${new Date().toLocaleTimeString()}: ${status}`;
        progressLog.appendChild(logEntry);
        progressLog.scrollTop = progressLog.scrollHeight;

        this.conversionState.progress = percentage;
        this.conversionState.status = status;
    }

    async validateEpub(epubData) {
        // Client-side EPUB validation
        // Check basic structure, manifest, etc.
        const validator = this.epubGenerator.createValidator();
        return await validator.validate(epubData);
    }

    async prepareDownload(epubData, filename) {
        // Create blob and download URL
        const blob = new Blob([epubData], { type: 'application/epub+zip' });
        const url = URL.createObjectURL(blob);

        this.downloadUrl = url;
        this.downloadFilename = `${filename}.epub`;
    }

    showDownloadButton() {
        const downloadBtn = document.getElementById('download-btn');
        downloadBtn.classList.remove('hidden');
        downloadBtn.onclick = () => this.downloadEpub();
    }

    downloadEpub() {
        if (!this.downloadUrl) return;

        const a = document.createElement('a');
        a.href = this.downloadUrl;
        a.download = this.downloadFilename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        // Clean up
        URL.revokeObjectURL(this.downloadUrl);
    }

    async initializeAI() {
        const aiService = this.settingsManager.get('ai.service', 'web-llm');

        if (aiService === 'web-llm') {
            try {
                await this.webLLM.initialize();
                this.updateModelStatus('ready', 'Model loaded');
            } catch (error) {
                console.warn('Failed to initialize Web LLM:', error);
                this.updateModelStatus('error', 'Failed to load');
            }
        }
    }

    async testAIConfiguration() {
        const testBtn = document.getElementById('test-ai');
        const originalText = testBtn.textContent;

        try {
            testBtn.textContent = 'Testing...';
            testBtn.disabled = true;

            const testContent = `Chapter 1: The Beginning

This is a test chapter to verify AI detection is working properly.

Chapter 2: The Middle

Another test chapter with different content.`;

            const result = await this.aiDetection.detectChapters(testContent);

            this.uiManager.showSuccess(`AI test successful! Detected ${result.length} chapters.`);

        } catch (error) {
            this.uiManager.showError(`AI test failed: ${error.message}`);
        } finally {
            testBtn.textContent = originalText;
            testBtn.disabled = false;
        }
    }

    handleAIServiceChange(service) {
        const webLLMSettings = document.getElementById('web-llm-settings');
        const apiSettings = document.getElementById('api-settings');

        webLLMSettings.classList.toggle('hidden', service !== 'web-llm');
        apiSettings.classList.toggle('hidden', service !== 'api');

        this.settingsManager.set('ai.service', service);
    }

    updateModelStatus(status, text) {
        const statusIndicator = document.getElementById('model-status');
        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');

        statusDot.className = `status-dot status-${status}`;
        statusText.textContent = text;
    }

    openSettings() {
        const modal = document.getElementById('settings-modal');
        modal.classList.remove('hidden');

        // Load current settings into form
        document.getElementById('auto-save-settings').checked =
            this.settingsManager.get('app.autoSave', true);
        document.getElementById('show-advanced-options').checked =
            this.settingsManager.get('app.showAdvanced', false);
        document.getElementById('ui-theme').value =
            this.settingsManager.get('ui.theme', 'light');
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.settingsManager.set('ui.theme', theme);
    }

    handleKeyboard(e) {
        // Keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'o':
                    e.preventDefault();
                    document.getElementById('file-input').click();
                    break;
                case 's':
                    e.preventDefault();
                    if (this.downloadUrl) this.downloadEpub();
                    break;
                case ',':
                    e.preventDefault();
                    this.openSettings();
                    break;
            }
        }

        // Escape key
        if (e.key === 'Escape') {
            // Close modals
            document.querySelectorAll('.modal').forEach(modal => {
                modal.classList.add('hidden');
            });
        }
    }

    formatFileSize(bytes) {
        const sizes = ['B', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 B';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.docx2shelf = new Docx2ShelfWeb();
});

// Service Worker registration for offline support
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}