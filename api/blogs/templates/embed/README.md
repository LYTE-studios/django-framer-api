# LYTE Blog Embed Documentation

## Table of Contents
1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Basic Implementation](#basic-implementation)
5. [Advanced Configuration](#advanced-configuration)
6. [Styling Guide](#styling-guide)
7. [SEO Considerations](#seo-considerations)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Quick Start

Add these two lines to your HTML:

```html
<script src="https://your-domain.com/path/to/blog-embed.js" type="module"></script>
<lyte-blog client-id="YOUR_CLIENT_ID"></lyte-blog>
```

## Prerequisites

1. You need a LYTE client ID (obtain this from your LYTE dashboard)
2. Your website must support JavaScript modules (all modern browsers do)
3. CORS must be properly configured on your LYTE API server

## Installation

### Step 1: Get the Files
Copy these files to your web server:
- `blog-embed.js` - The main embed script
- `blog-embed.html` - (Optional) Example implementation

### Step 2: Host the Files
Upload the `blog-embed.js` file to your web server. Common locations:
```
/assets/js/blog-embed.js
/static/js/blog-embed.js
/scripts/blog-embed.js
```

### Step 3: Configure CORS
Ensure your LYTE API server allows requests from your domain. Contact the LYTE team if you need help with this.

## Basic Implementation

### 1. Add the Script
Place this in your HTML `<head>` section:
```html
<script src="/path/to/blog-embed.js" type="module"></script>
```

### 2. Add the Component
Place this where you want the blog posts to appear:
```html
<lyte-blog 
    client-id="YOUR_CLIENT_ID" 
    theme="light" 
    posts-per-page="10">
    <noscript>
        Please enable JavaScript to view our blog posts.
    </noscript>
</lyte-blog>
```

## Advanced Configuration

### Available Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| client-id | string | required | Your LYTE client ID |
| theme | string | "light" | Theme ("light" or "dark") |
| posts-per-page | number | 10 | Number of posts to display |

### Example with All Options
```html
<lyte-blog 
    client-id="YOUR_CLIENT_ID" 
    theme="dark" 
    posts-per-page="5">
</lyte-blog>
```

## Styling Guide

### CSS Variables
You can customize the appearance by overriding these CSS variables:

```css
lyte-blog {
    --post-bg: #ffffff;        /* Post background color */
    --title-color: #1a1a1a;    /* Post title color */
    --text-color: #4a4a4a;     /* Post content color */
    --date-color: #666666;     /* Publication date color */
}
```

### Dark Theme Variables
```css
lyte-blog[theme="dark"] {
    --post-bg: #2d2d2d;
    --title-color: #ffffff;
    --text-color: #e0e0e0;
    --date-color: #a0a0a0;
}
```

### Custom Styling Example
```css
/* Custom container width */
lyte-blog {
    max-width: 1200px;
    margin: 0 auto;
}

/* Custom grid layout */
lyte-blog::part(grid) {
    grid-template-columns: repeat(2, 1fr);
    gap: 3rem;
}
```

## SEO Considerations

1. **Content Visibility**
   - The embed uses semantic HTML5 elements
   - Content is visible even without JavaScript
   - Proper meta tags and datetime attributes
   - Alt text for images

2. **Noscript Fallback**
   - Always include a noscript tag with alternative content
   - Consider linking to your main blog page

3. **Best Practices**
   - Use descriptive alt text for thumbnails
   - Keep titles and content relevant
   - Ensure proper heading hierarchy

## Troubleshooting

### Common Issues

1. **Posts Not Loading**
   - Check if your client ID is correct
   - Verify CORS configuration
   - Check browser console for errors
   - Ensure API endpoint is accessible

2. **Styling Issues**
   - Check for CSS conflicts
   - Verify theme attribute is set correctly
   - Inspect shadow DOM for styling issues

3. **Performance Issues**
   - Reduce posts-per-page
   - Optimize thumbnail images
   - Consider lazy loading

### Debug Mode
Add `debug="true"` to see detailed logs:
```html
<lyte-blog client-id="YOUR_CLIENT_ID" debug="true"></lyte-blog>
```

## Best Practices

1. **Performance**
   - Load the script asynchronously
   - Set reasonable posts-per-page
   - Use appropriate image sizes

2. **Accessibility**
   - Include alt text for images
   - Maintain color contrast
   - Use semantic HTML

3. **Responsive Design**
   - Test on multiple devices
   - Use flexible grid layouts
   - Optimize for mobile

4. **Error Handling**
   - Always include noscript fallback
   - Handle API errors gracefully
   - Provide user feedback

5. **Maintenance**
   - Keep the embed script updated
   - Monitor API endpoint health
   - Review and update content regularly

For additional support or custom implementations, contact the LYTE support team.