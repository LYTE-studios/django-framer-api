class LyteBlogEmbed extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    static get observedAttributes() {
        return ['client-id', 'theme', 'posts-per-page'];
    }

    async connectedCallback() {
        const clientId = this.getAttribute('client-id');
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
                .error {
                    color: #e53e3e;
                    padding: 1rem;
                    text-align: center;
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
                <slot></slot>
            </div>
        `;

        try {
            const response = await fetch(`/api/clients/${clientId}/posts/`);
            if (!response.ok) throw new Error('Failed to fetch posts');
            
            const posts = await response.json();
            this.shadowRoot.querySelector('.blog-grid').innerHTML = posts
                .slice(0, postsPerPage)
                .map(post => `
                    <article class="blog-post">
                        ${post.thumbnail ? `<img src="${post.thumbnail}" alt="${post.title}">` : ''}
                        <div class="blog-post-content">
                            <h2>${post.title}</h2>
                            <p>${this.truncateContent(post.content)}</p>
                            <time datetime="${post.published_at}">${this.formatDate(post.published_at)}</time>
                        </div>
                    </article>
                `).join('');
        } catch (error) {
            this.shadowRoot.querySelector('.blog-grid').innerHTML = `
                <div class="error">Failed to load blog posts. Please try again later.</div>
            `;
            console.error('Error loading blog posts:', error);
        }
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
}

customElements.define('lyte-blog', LyteBlogEmbed);