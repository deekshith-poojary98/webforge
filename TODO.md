# TODO List

## Branding
- [x] Official name: WebForge
- [x] Create logo
- [x] Design color scheme
- [x] Create favicon
- [x] Design landing page
- [x] Write tagline and description

## Editor Enhancements
- [x] Add line numbers to YAML editor
  - Show line numbers in the gutter
  - Custom styling for line numbers
  - Option to toggle visibility
  - Proper alignment and padding

- [ ] Implement code folding
  - Fold/unfold sections based on YAML indentation
  - Visual indicators for foldable sections
  - Keyboard shortcuts for folding
  - Remember fold state between sessions
  - Support for nested folds

- [ ] Add indent guide lines
  - Show vertical lines for each indentation level
  - Customizable colors and styles
  - Option to toggle visibility
  - Proper alignment with content
  - Support for different indentation sizes

- [ ] Editor UI Improvements
  - Custom scrollbar styling
  - Current line highlighting
  - Selection highlighting
  - Bracket matching
  - Auto-indentation
  - Tab size configuration
  - Word wrap options

## Syntax Highlighting Issues
- [ ] Fix `text-decoration` CSS property highlighting (currently appears white instead of coral)
  - Issue: The regex pattern for CSS properties is not properly matching hyphenated properties
  - Location: `main.py` in `YAMLHighlighter` class
  - Current pattern: `r'^\s*[a-z-]+(?=:)'`
  - Need to investigate why the pattern isn't working as expected

## Future Improvements
- [ ] Add more comprehensive CSS property highlighting
- [ ] Consider adding different colors for different types of CSS properties (e.g., layout vs. typography)
- [ ] Add support for CSS units highlighting (px, em, rem, etc.)
- [ ] Add support for CSS color values highlighting
- [ ] Add support for CSS function highlighting (e.g., rgba(), calc(), etc.)
- [ ] Add support for sudo classes (e.g., :hover, :focus, :active) in CSS styling
  - Highlight sudo classes with distinct color
  - Support for common sudo classes
  - Support for custom sudo classes
  - Proper syntax validation

## Code Organization
- [ ] Consider splitting the syntax highlighting rules into a separate configuration file
- [ ] Add more comments explaining the regex patterns
- [ ] Add unit tests for syntax highlighting

## Documentation
- [ ] Add documentation about supported YAML syntax
- [ ] Add documentation about supported CSS properties
- [ ] Add examples of different component types and their styling options

# YAML to HTML Converter - Future Components

## High Priority Components

### Navigation
- `navbar` - Navigation bar with logo, links, and mobile menu support
  - Support for dropdown menus
  - Mobile-responsive hamburger menu
  - Sticky/fixed positioning options
  - Custom styling for active/inactive states

### Layout
- `grid` - CSS Grid container for complex layouts
  - Define columns and rows
  - Gap control
  - Auto-fit/auto-fill options
  - Responsive breakpoints
- `flex` - Flexbox container for flexible layouts
  - Direction control (row/column)
  - Justify and align options
  - Wrap behavior
  - Gap control

### Media
- `video` - Video player component
  - Support for local and remote videos
  - Custom controls
  - Thumbnail preview
  - Autoplay options
- `carousel` - Image carousel/slider
  - Auto-play option
  - Navigation controls
  - Touch/swipe support
  - Custom transitions

### Forms
- `form` - Form container with validation
  - Input fields (text, email, number, etc.)
  - Checkboxes and radio buttons
  - Select dropdowns
  - File upload
  - Submit button
  - Form validation
  - Error messages

## Medium Priority Components

### Content
- `card` - Card component for content display
  - Header, body, and footer sections
  - Image support
  - Hover effects
  - Shadow options
- `accordion` - Collapsible content sections
  - Multiple sections
  - Custom icons
  - Animation options
  - Nested content support

### Interactive
- `tabs` - Tabbed content interface
  - Multiple tabs
  - Custom styling
  - Content switching
  - Responsive design
- `modal` - Popup dialog box
  - Custom triggers
  - Backdrop options
  - Animation effects
  - Close behaviors

### Data Display
- `table` - Data table component
  - Sorting functionality
  - Pagination
  - Responsive design
  - Custom styling
- `progress` - Progress indicators
  - Linear progress bars
  - Circular progress
  - Custom colors
  - Animation options

## Low Priority Components

### Social
- `social-share` - Social media sharing buttons
  - Multiple platform support
  - Custom icons
  - Share counts
  - Custom URLs
- `social-feed` - Social media feed display
  - Platform integration
  - Post formatting
  - Update frequency
  - Custom styling

### Advanced
- `map` - Interactive map component
  - Multiple providers (Google, OpenStreetMap)
  - Custom markers
  - Zoom controls
  - Custom styling
- `chart` - Data visualization
  - Multiple chart types
  - Data binding
  - Animation options
  - Responsive design

### Utility
- `breadcrumb` - Navigation breadcrumbs
  - Dynamic generation
  - Custom separators
  - Responsive design
- `pagination` - Page navigation
  - Custom styling
  - Page numbers
  - Previous/Next buttons
  - Ellipsis for long ranges

## Implementation Notes

### Priority Considerations
1. Focus on components that enhance basic page structure
2. Prioritize components that are commonly used in web design
3. Consider mobile responsiveness in all new components
4. Ensure consistent styling API across all components

### Technical Requirements
- Each component should:
  - Support custom styling
  - Be responsive by default
  - Include proper accessibility attributes
  - Have clear documentation
  - Include example usage
  - Support nesting where appropriate

### Documentation Needs
- Clear examples for each component
- Style customization options
- Responsive behavior details
- Accessibility considerations
- Browser compatibility notes

## Future Enhancements

### Component Features
- Add animation support to all components
- Implement dark/light theme variants
- Add more interactive behaviors
- Enhance accessibility features
- Add more customization options

### Developer Experience
- Add component playground
- Create component templates
- Add component testing suite
- Improve error handling
- Add component validation 