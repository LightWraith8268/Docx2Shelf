/**
 * Web LLM Client for browser-based AI processing
 * Uses WebLLM or similar libraries for in-browser AI inference
 */

export class WebLLMClient {
    constructor() {
        this.model = null;
        this.isInitialized = false;
        this.isLoading = false;
        this.availableModels = [
            {
                id: 'phi-2',
                name: 'Phi-2',
                size: '2.7B',
                description: 'Small, fast model for basic tasks',
                downloadSize: '1.5GB'
            },
            {
                id: 'gemma-2b',
                name: 'Gemma 2B',
                size: '2B',
                description: 'Balanced performance and accuracy',
                downloadSize: '1.2GB'
            },
            {
                id: 'llama-7b',
                name: 'Llama 7B',
                size: '7B',
                description: 'Large model for high accuracy',
                downloadSize: '4.2GB'
            }
        ];
    }

    async initialize(modelId = 'phi-2') {
        if (this.isInitialized) return;

        try {
            this.isLoading = true;
            console.log(`Initializing Web LLM with model: ${modelId}`);

            // Check if WebLLM is available
            if (typeof window.webllm === 'undefined') {
                // Dynamically load WebLLM library
                await this.loadWebLLM();
            }

            // Initialize the model
            await this.loadModel(modelId);

            this.isInitialized = true;
            this.isLoading = false;

            console.log('Web LLM initialized successfully');

        } catch (error) {
            this.isLoading = false;
            console.error('Failed to initialize Web LLM:', error);
            throw new Error(`Web LLM initialization failed: ${error.message}`);
        }
    }

    async loadWebLLM() {
        // Load WebLLM library from CDN or local copy
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/@mlc-ai/web-llm@0.2.0/lib/index.js';
            script.type = 'module';
            script.onload = resolve;
            script.onerror = () => {
                // Fallback to local simulation
                console.warn('WebLLM not available, using simulation mode');
                window.webllm = this.createSimulatedWebLLM();
                resolve();
            };
            document.head.appendChild(script);
        });
    }

    createSimulatedWebLLM() {
        // Simulated WebLLM for development/testing
        return {
            CreateMLCEngine: async () => ({
                reload: async (modelId) => {
                    console.log(`Simulating model load: ${modelId}`);
                    // Simulate loading time
                    await new Promise(resolve => setTimeout(resolve, 2000));
                },
                chat: {
                    completions: {
                        create: async (request) => {
                            console.log('Simulating AI completion:', request);

                            // Simulate AI response for chapter detection
                            const content = request.messages?.[0]?.content || '';
                            const chapters = this.simulateChapterDetection(content);

                            return {
                                choices: [{
                                    message: {
                                        content: JSON.stringify({
                                            boundaries: chapters
                                        })
                                    }
                                }]
                            };
                        }
                    }
                }
            })
        };
    }

    simulateChapterDetection(content) {
        // Simple heuristic chapter detection for simulation
        const chapters = [];
        const lines = content.split('\n');

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();

            // Look for chapter patterns
            if (line.match(/^(chapter|chap\.?)\s+\d+/i) ||
                line.match(/^(part|book)\s+\d+/i) ||
                line.match(/^[A-Z][A-Z\s]{5,}$/)) {

                chapters.push({
                    position: content.indexOf(line),
                    title: line.substring(0, 50),
                    confidence: 0.85
                });
            }
        }

        return chapters;
    }

    async loadModel(modelId) {
        try {
            // Create engine
            this.engine = await window.webllm.CreateMLCEngine();

            // Load specified model
            await this.engine.reload(modelId);

            this.currentModelId = modelId;

            // Dispatch progress events
            this.dispatchProgress('Model loaded successfully', 100);

        } catch (error) {
            throw new Error(`Failed to load model ${modelId}: ${error.message}`);
        }
    }

    async detectChapters(content) {
        if (!this.isInitialized) {
            throw new Error('Web LLM not initialized');
        }

        try {
            const prompt = this.createChapterDetectionPrompt(content);

            const response = await this.engine.chat.completions.create({
                messages: [
                    {
                        role: "system",
                        content: "You are a document analysis expert. Analyze text and identify chapter boundaries."
                    },
                    {
                        role: "user",
                        content: prompt
                    }
                ],
                temperature: 0.1,
                max_tokens: 1000
            });

            const result = response.choices[0].message.content;
            return this.parseChapterResponse(result);

        } catch (error) {
            console.error('Chapter detection failed:', error);
            throw new Error(`AI chapter detection failed: ${error.message}`);
        }
    }

    createChapterDetectionPrompt(content) {
        // Limit content size for processing
        const maxLength = 10000;
        const truncatedContent = content.length > maxLength ?
            content.substring(0, maxLength) + '...' : content;

        return `Analyze this document and identify chapter boundaries. Look for:
1. Chapter headings (Chapter 1, Chapter One, etc.)
2. Part divisions (Part I, Part II, etc.)
3. Natural content breaks and transitions
4. Section headers

Return a JSON array with this format:
{
  "boundaries": [
    {
      "position": 0,
      "title": "Chapter Title",
      "confidence": 0.9
    }
  ]
}

Document content:
${truncatedContent}`;
    }

    parseChapterResponse(response) {
        try {
            // Try to extract JSON from response
            const jsonMatch = response.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                const data = JSON.parse(jsonMatch[0]);
                return data.boundaries || [];
            }

            // Fallback: parse text response
            return this.parseTextResponse(response);

        } catch (error) {
            console.warn('Failed to parse AI response, using fallback:', error);
            return [];
        }
    }

    parseTextResponse(response) {
        // Extract chapter information from text response
        const chapters = [];
        const lines = response.split('\n');

        for (const line of lines) {
            if (line.toLowerCase().includes('chapter') ||
                line.toLowerCase().includes('part')) {

                // Extract chapter info
                const match = line.match(/(\d+)/);
                const position = match ? parseInt(match[1]) * 1000 : 0; // Rough estimate

                chapters.push({
                    position: position,
                    title: line.trim().substring(0, 50),
                    confidence: 0.7
                });
            }
        }

        return chapters;
    }

    async generateMetadata(content) {
        if (!this.isInitialized) {
            throw new Error('Web LLM not initialized');
        }

        try {
            const prompt = `Analyze this document and suggest metadata:

Content preview:
${content.substring(0, 2000)}...

Suggest:
1. Genre (Fiction, Non-fiction, etc.)
2. Brief description (2-3 sentences)
3. Key themes or topics

Return JSON format:
{
  "genre": "Fiction",
  "description": "A brief description...",
  "themes": ["theme1", "theme2"]
}`;

            const response = await this.engine.chat.completions.create({
                messages: [
                    {
                        role: "system",
                        content: "You are a literary analysis expert. Analyze documents and suggest appropriate metadata."
                    },
                    {
                        role: "user",
                        content: prompt
                    }
                ],
                temperature: 0.3,
                max_tokens: 500
            });

            const result = response.choices[0].message.content;
            return this.parseMetadataResponse(result);

        } catch (error) {
            console.error('Metadata generation failed:', error);
            return {};
        }
    }

    parseMetadataResponse(response) {
        try {
            const jsonMatch = response.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            }
        } catch (error) {
            console.warn('Failed to parse metadata response:', error);
        }

        return {};
    }

    getAvailableModels() {
        return this.availableModels;
    }

    getCurrentModel() {
        return this.currentModelId;
    }

    isReady() {
        return this.isInitialized && !this.isLoading;
    }

    getStatus() {
        if (this.isLoading) return 'loading';
        if (this.isInitialized) return 'ready';
        return 'not-initialized';
    }

    dispatchProgress(message, percentage) {
        const event = new CustomEvent('webllm-progress', {
            detail: { message, percentage }
        });
        window.dispatchEvent(event);
    }

    // Memory management
    async cleanup() {
        if (this.engine) {
            try {
                // Clean up model resources
                await this.engine.unload();
            } catch (error) {
                console.warn('Error during cleanup:', error);
            }
        }

        this.isInitialized = false;
        this.model = null;
        this.engine = null;
    }
}