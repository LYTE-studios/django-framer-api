# Blovio Blog Embed System

A lightweight, customizable blog embed system that allows you to display your Blovio-generated blog posts on any website.

## Features

- 🎨 Automatic light/dark theme support
- 📱 Fully responsive design
- 🔒 Secure embed token system
- ⚡ Fast loading with optimized performance
- 🖼️ Thumbnail image support
- 📊 Subscription status handling

## Quick Start

1. Get your embed token from your LYTE dashboard
2. Add the script to your HTML:
```html
<script src="https://your-domain.com/path/to/blog-embed.js" type="module"></script>
```

3. Add the blog component where you want your posts to appear:
```html
<lyte-blog 
    data-token="YOUR_EMBED_TOKEN" 
    theme="light" 
    posts-per-page="10">
    <noscript>
        Please enable JavaScript to view our blog posts.
    </noscript>
</lyte-blog>
```

## Component Attributes

| Attribute | Required | Default | Description |
|-----------|----------|---------|-------------|
| data-token | Yes | - | Your unique embed token from LYTE dashboard |
| theme | No | "light" | Color theme ("light" or "dark") |
| posts-per-page | No | 10 | Number of posts to display (max 50) |

## Subscription Requirements

The embed system is tied to your LYTE subscription:

- **Active Subscription**: Blog posts will display normally
- **Trial Period**: Full access during the trial period
- **Expired/Cancelled**: Posts will not be displayed, and a subscription message will appear
- **Past Due**: Posts will not be displayed until payment is resolved

## Security

- Embed tokens are unique to each client
- Tokens can be regenerated from the LYTE dashboard
- Tokens automatically expire when subscription becomes inactive
- All requests are rate-limited and monitored for abuse

## Error States

The embed system handles various states gracefully:

- **Loading**: Shows a loading spinner while fetching posts
- **Empty**: Displays a message when no posts are available
- **Error**: Shows error message if posts can't be loaded
- **Subscription Required**: Indicates when subscription is needed

## Browser Support

- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

## Performance

- Lazy loading of images
- Minimal bundle size (~10KB gzipped)
- No external dependencies
- Optimized for Core Web Vitals

## Customization

The embed system automatically inherits your website's font settings and provides a responsive layout that adapts to your design. For advanced customization needs:

1. **Theme Colors**: Use the built-in light/dark themes
2. **Layout**: Responsive grid automatically adjusts to container width
3. **Typography**: Inherits from your website's font settings
4. **Custom Styling**: Available through LYTE Enterprise plans

## Troubleshooting

1. **Posts Not Displaying**
   - Verify your embed token is correct
   - Check your subscription status
   - Ensure JavaScript is enabled
   - Check browser console for errors

2. **Style Conflicts**
   - The component uses Shadow DOM to prevent style leakage
   - Contact support if you notice any styling issues

3. **Performance Issues**
   - Reduce posts-per-page if loading is slow
   - Ensure images are being cached properly
   - Check network tab for any bottlenecks

## Support

- Documentation: https://docs.lytestudios.com/embed
- Email: support@lytestudios.com
- Dashboard: https://dashboard.lytestudios.com

## Updates

The embed system is automatically updated with new features and security patches. No action is required from your side to receive updates.