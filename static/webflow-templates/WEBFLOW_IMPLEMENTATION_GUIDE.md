# Proven Connections Search - Webflow Implementation Guide

## Step 1: Webflow Setup

1. Create a new page in your Webflow project
2. Add a new section with class `search-section`
3. Copy the structure from `search-section.html` into Webflow's designer
4. Add the styles from `styles.css` to Webflow's style manager

## Step 2: Required External Resources

Add these to your page settings under "Custom Code" in the `<head>` tag:

```html
<!-- jQuery -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

<!-- Select2 for autocomplete -->
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>

<!-- Custom styles for Select2 -->
<style>
.select2-container .select2-selection--single {
    height: 38px;
    border-radius: 6px;
    border-color: #e5e7eb;
}

.select2-container--default .select2-selection--single .select2-selection__rendered {
    line-height: 38px;
    padding-left: 12px;
    color: #1a1a1a;
}

.select2-container--default .select2-selection--single .select2-selection__arrow {
    height: 36px;
}

.select2-dropdown {
    border-color: #e5e7eb;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.select2-search--dropdown .select2-search__field {
    padding: 8px;
    border-radius: 4px;
}

.select2-results__option {
    padding: 8px 12px;
}
</style>
```

## Step 3: Add JavaScript Code

Add this before the closing `</body>` tag in your page settings:

```html
<script>
// Replace with your actual API endpoint
const API_ENDPOINT = 'YOUR_API_ENDPOINT';

// Import and initialize the search functionality
const script = document.createElement('script');
script.src = `${API_ENDPOINT}/static/webflow-script.js`;
document.body.appendChild(script);
</script>
```

## Step 4: Class Names to Maintain

Ensure these class names are exactly as specified in your Webflow elements:

- `vendor-search-input`
- `client-search-input`
- `vendor-results`
- `client-results`
- `vendor-stats-container`
- `client-stats-container`
- `company-card-template`
- `stats-template`

## Step 5: Testing

1. Deploy your backend API to a hosting service
2. Update the `API_ENDPOINT` in your Webflow page settings
3. Test the search functionality:
   - Autocomplete should work for both vendors and clients
   - Results should display in cards with logos and locations
   - Stats should update with each search

## Common Issues

1. CORS Errors:
   - Ensure your API's CORS settings include your Webflow domain
   - Update the `allow_origins` in your FastAPI app

2. Select2 Not Working:
   - Check if jQuery is loaded before Select2
   - Verify class names match exactly

3. Results Not Displaying:
   - Check browser console for errors
   - Verify API endpoint is correct and accessible
   - Ensure template elements exist with correct classes

## Customization

### Styling

- All styles are customizable through Webflow's style manager
- Colors use a consistent palette that you can modify
- Responsive breakpoints can be adjusted in Webflow

### Templates

- Card templates can be modified in Webflow's designer
- Maintain the class names for JavaScript functionality
- Add additional fields as needed

## Security Considerations

1. API Access:
   - Consider implementing API key authentication
   - Use environment variables for sensitive data
   - Implement rate limiting on your API

2. Data Privacy:
   - Consider what company information to display publicly
   - Add user authentication if needed
   - Implement data access controls

## Performance Tips

1. Enable Webflow's cache settings
2. Optimize company logos for web use
3. Use the API's built-in pagination
4. Leverage the caching system in the API

## Support

For technical support or questions:
1. Check the API documentation
2. Review browser console for errors
3. Contact the development team
