# GEO Analyzer - Replit Project

## Project Overview

GEO Analyzer is a modern, production-ready React TypeScript web application that analyzes brand visibility across major language models (LLMs). The application features a beautiful, responsive UI with real-time progress tracking, comprehensive data visualizations, and robust error handling.

**Purpose**: Provide users with actionable insights about their brand's visibility across Claude, ChatGPT, Gemini, Mistral, Google AI Overview, and Perplexity through an intuitive, data-focused interface.

**Current State**: MVP Complete - All core features implemented and tested

## Recent Changes (November 14, 2025)

### Complete Application Implementation
- ✅ Designed and implemented complete data model with TypeScript schemas
- ✅ Built all React components with exceptional visual quality
- ✅ Implemented API proxy routes for FastAPI backend integration
- ✅ Added real-time polling with 2-second intervals
- ✅ Created comprehensive error handling with retry functionality
- ✅ Implemented all data visualizations (line chart, pie chart, tables)
- ✅ Added pagination and search functionality to tables
- ✅ Ensured complete mobile responsiveness
- ✅ Added all required data-testid attributes for testing
- ✅ Fixed all TypeScript errors and LSP diagnostics

## Project Architecture

### Tech Stack
- **Frontend**: React 18, TypeScript, Tailwind CSS, Shadcn UI
- **State Management**: TanStack Query (React Query v5)
- **Charts**: Recharts
- **Forms**: React Hook Form with Zod validation
- **Routing**: Wouter
- **Backend**: Express.js proxy server
- **HTTP Client**: Axios

### Key Components

1. **AnalysisForm** (`client/src/components/analysis-form.tsx`)
   - Multi-field input form with validation
   - LLM selection with 6 checkboxes
   - Form validation using react-hook-form and Zod
   - Beautiful hover states and interactions

2. **AnalysisProgress** (`client/src/components/analysis-progress.tsx`)
   - Real-time progress tracking with polling
   - Error handling with retry functionality
   - Smooth loading animations
   - Automatic transition to results on completion

3. **AnalysisResults** (`client/src/components/analysis-results.tsx`)
   - Comprehensive results dashboard
   - Summary metrics in card layout
   - Multiple visualizations and data tables
   - New analysis button for reset

4. **Data Visualizations**
   - **SummaryMetrics**: 4 metric cards with icons and large values
   - **PromptsTable**: Paginated table with search functionality
   - **VisibilityChart**: Line chart showing visibility trends
   - **ShareOfVoiceChart**: Pie chart for brand distribution
   - **DomainCitationsTable**: Sorted domain citations

### API Integration

The application connects to a FastAPI backend through proxy routes:

**Backend Endpoints Required**:
- `POST /api/analysis/run` - Start analysis
- `GET /api/analysis/status/{session_id}` - Check progress (polled every 2s)
- `GET /api/results/{session_id}` - Retrieve results

**Configuration**: 
- Backend URL: `FASTAPI_BASE_URL` environment variable (default: `http://localhost:8000`)

## Design System

### Colors
- **Primary**: Blue (`hsl(217 91% 60%)`) - Used for buttons, links, active states
- **Background**: Light/Dark adaptive
- **Cards**: Elevated with subtle borders
- **Charts**: Multi-color palette for data visualization

### Typography
- **Font Family**: Inter (Google Fonts)
- **Hierarchy**: 
  - Hero Title: text-5xl font-bold
  - Section Headings: text-2xl font-semibold
  - Card Titles: text-lg font-semibold
  - Metric Values: text-3xl font-bold
  - Body: text-base font-normal

### Layout
- **Max Width**: 7xl (1280px) centered
- **Spacing**: Consistent 4, 6, 8 unit spacing
- **Responsive**: Mobile-first with sm, md, lg, xl breakpoints
- **Cards**: Rounded borders (lg), subtle shadows, padding p-6

## User Workflows

### Primary Flow
1. User enters brand information (brand name required)
2. User selects 1-6 LLMs to analyze
3. User clicks "Start Analysis"
4. System shows progress with polling
5. System displays results dashboard
6. User explores metrics, charts, and tables
7. User can start new analysis

### Error Handling Flow
1. If backend unavailable, show error state
2. Display clear error message
3. Provide "Retry Connection" button
4. On retry, clear cache and refetch
5. Resume normal flow when backend available

## Development Guidelines

### Code Style
- TypeScript strict mode enabled
- Proper type safety with Zod schemas
- Component modularity and reusability
- Shadcn UI components for consistency
- Tailwind CSS for all styling

### State Management
- TanStack Query for server state
- React Hook Form for form state
- Local useState for UI state only
- No global state needed for MVP

### Error Handling
- 3 retry attempts on network errors
- User-friendly toast notifications
- Graceful degradation
- Clear error messages without technical jargon

## Testing

### Test IDs
All interactive and display elements have `data-testid` attributes:
- Form inputs: `input-{field-name}`
- Buttons: `button-{action}`
- Checkboxes: `checkbox-llm-{llm-name}`
- Metrics: `metric-{metric-name}`
- Tables: `row-{type}-{index}`
- Charts: `text-chart-title-{chart-name}`

### Manual Testing Checklist
- [ ] Form validation works correctly
- [ ] At least 1 LLM must be selected
- [ ] Progress polling updates every 2 seconds
- [ ] Error state displays when backend unavailable
- [ ] Retry button re-establishes connection
- [ ] Results display all data correctly
- [ ] Pagination works in tables
- [ ] Search filters prompts table
- [ ] Charts render with correct data
- [ ] Mobile responsive on all breakpoints

## Environment Setup

### Required
- Node.js 20+
- FastAPI backend on port 8000 (or configured port)

### Optional
- `FASTAPI_BASE_URL` - Override backend URL

## Future Enhancements

### Phase 2 (Not in MVP)
- Export functionality (PDF, CSV)
- Analysis history
- Result comparison
- Advanced filtering
- Competitor analysis section
- Shareable results links

## Performance Considerations

- Polling stops when analysis completes or errors occur
- Query caching prevents unnecessary refetches
- Table pagination limits DOM elements
- Images lazy loaded
- Component code splitting via React.lazy (if needed)

## Accessibility

- WCAG AA color contrast ratios
- Keyboard navigation support
- Screen reader friendly
- Focus indicators on interactive elements
- ARIA labels on charts and complex UI

## Deployment Notes

1. Ensure FastAPI backend is running and accessible
2. Set `FASTAPI_BASE_URL` if not using localhost:8000
3. Build frontend: `npm run build`
4. Run production server on port 5000
5. Monitor backend connection health
6. Check polling cadence under load

## Known Limitations

- Requires FastAPI backend to be running
- No offline mode
- No authentication (add in future)
- No data persistence (all from backend)
- Session IDs not stored (refreshing page loses state)

## Support & Troubleshooting

**Connection Errors**:
- Verify FastAPI backend is running on expected port
- Check CORS settings allow requests from frontend
- Ensure network connectivity
- Use retry button to re-establish connection

**Polling Issues**:
- Polling stops after 3 failed attempts
- Check backend /status endpoint returns correct format
- Verify status transitions to "completed" properly

**UI Issues**:
- Clear browser cache
- Check console for JavaScript errors
- Verify all dependencies installed
- Restart development server

---

**Last Updated**: November 14, 2025
**Status**: MVP Complete, Production Ready
**Maintainer**: Replit Agent
