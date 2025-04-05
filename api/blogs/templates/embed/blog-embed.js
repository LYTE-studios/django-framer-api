class LyteBlogEmbed extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    static get observedAttributes() {
        return ['data-token', 'theme', 'posts-per-page'];
    }

    async connectedCallback() {
        const token = this.getAttribute('data-token');
        const theme = this.getAttribute('theme') || 'light';
        const postsPerPage = parseInt(this.getAttribute('posts-per-page')) || 10;

        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: system-ui, -apple-system, sans-serif;
                }
                .blog-grid {
                    display: grid;
                    gap: 2rem;
                    padding: 1rem;
                }
                .blog-post {
                    background: var(--post-bg, #fff);
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    overflow: hidden;
                    transition: transform 0.2s;
                }
                .blog-post:hover {
                    transform: translateY(-2px);
                }
                .blog-post img {
                    width: 100%;
                    height: 200px;
                    object-fit: cover;
                }
                .blog-post-content {
                    padding: 1.5rem;
                }
                .blog-post h2 {
                    margin: 0 0 1rem;
                    font-size: 1.5rem;
                    color: var(--title-color, #1a1a1a);
                }
                .blog-post p {
                    margin: 0;
                    color: var(--text-color, #4a4a4a);
                    line-height: 1.6;
                }
                .blog-post time {
                    display: block;
                    margin-top: 1rem;
                    color: var(--date-color, #666);
                    font-size: 0.875rem;
                }
                .message {
                    padding: 2rem;
                    text-align: center;
                    border-radius: 8px;
                    margin: 1rem;
                }
                .error {
                    background-color: #fee2e2;
                    color: #dc2626;
                    border: 1px solid #fecaca;
                }
                .loading {
                    background-color: #f3f4f6;
                    color: #4b5563;
                }
                .subscription-error {
                    background-color: #fef3c7;
                    color: #d97706;
                    border: 1px solid #fde68a;
                }
                .loading-spinner {
                    display: inline-block;
                    width: 2rem;
                    height: 2rem;
                    border: 3px solid #e5e7eb;
                    border-radius: 50%;
                    border-top-color: #6b7280;
                    animation: spin 1s linear infinite;
                    margin-bottom: 1rem;
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                /* Theme: Dark */
                :host([theme="dark"]) {
                    --post-bg: #2d2d2d;
                    --title-color: #ffffff;
                    --text-color: #e0e0e0;
                    --date-color: #a0a0a0;
                }
                /* Responsive Grid */
                @media (min-width: 768px) {
                    .blog-grid {
                        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    }
                }
            </style>
            <div class="blog-grid">
                <div class="message loading">
                    <div class="loading-spinner"></div>
                    <p>Loading blog posts...</p>
                </div>
            </div>
        `;

        if (!token) {
            this.showError('No embed token provided. Please check your integration code.');
            return;
        }

        try {
            const response = await fetch(`/api/blogs/posts/?embed_token=${encodeURIComponent(token)}`);
            
            if (response.status === 402) {
                this.showSubscriptionError();
                return;
            }
            
            if (!response.ok) {
                throw new Error('Failed to fetch posts');
            }
            
            const data = await response.json();
            
            if (!data.results || !data.results.length) {
                this.shadowRoot.querySelector('.blog-grid').innerHTML = `
                    <div class="message">No blog posts available yet.</div>
                `;
                return;
            }

            this.shadowRoot.querySelector('.blog-grid').innerHTML = data.results
                .slice(0, postsPerPage)
                .map(post => `
                    <article class="blog-post">
                        ${post.thumbnail ? `<img src="${this.escapeHtml(post.thumbnail)}" alt="${this.escapeHtml(post.title)}">` : ''}
                        <div class="blog-post-content">
                            <h2>${this.escapeHtml(post.title)}</h2>
                            <p>${this.escapeHtml(this.truncateContent(post.content))}</p>
                            <time datetime="${post.published_at}">${this.formatDate(post.published_at)}</time>
                        </div>
                    </article>
                `).join('');
        } catch (error) {
            this.showError('Failed to load blog posts. Please try again later.');
            console.error('Error loading blog posts:', error);
        }
    }

    showError(message) {
        this.shadowRoot.querySelector('.blog-grid').innerHTML = `
            <div class="message error">
                <p>${this.escapeHtml(message)}</p>
            </div>
        `;
    }

    showSubscriptionError() {
        this.shadowRoot.querySelector('.blog-grid').innerHTML = `
            <div class="message subscription-error">
                <p>This blog feed is currently inactive. Please check your subscription status.</p>
            </div>
        `;
    }

    truncateContent(content) {
        const words = content.split(' ').slice(0, 30);
        return words.join(' ') + (words.length >= 30 ? '...' : '');
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

customElements.define('lyte-blog', LyteBlogEmbed);