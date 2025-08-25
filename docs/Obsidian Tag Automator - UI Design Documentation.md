# Obsidian Tag Automator - UI Design Documentation

## Overview
The Obsidian Tag Automator is a powerful tool that helps users manage and organize tags in their Obsidian vault using AI-powered suggestions. This document outlines the app's functionality, user flows, and technical considerations to guide UI designers in creating a new interface.

## 1. Core Purpose
The app automates the process of adding relevant tags to Obsidian notes by:
- Analyzing note content using AI (Google Gemini)
- Suggesting appropriate tags based on content
- Managing existing tags (renaming, merging, deleting)
- Validating tag consistency across the vault
- Creating aliases for similar tags

## 2. User Journey & Key Features

### 2.1 Dashboard (Home Screen)
**Purpose**: Provide an at-a-glance overview of vault status and recent activity

**User Flow**:
1. User opens the app and lands on the dashboard
2. Dashboard displays:
   - Vault path and AI status (online/offline)
   - Statistics: total files, tagged files, unique tags
   - Recent activity: list of recently modified files
3. User can refresh data using a button

**Technical Notes**:
- Data comes from three API endpoints: `/api/status`, `/api/files`, `/api/tags`
- Dashboard auto-refreshes every 10 seconds when active
- Shows loading states while data is being fetched

### 2.2 Tag Automator (Core Feature)
**Purpose**: Automatically process files to add/update tags using AI

**User Flow**:
1. User navigates to "Tag Automator" view
2. User selects processing options:
   - **Re-tagging Strategy**:
     - Only process files that have NOT been AI-tagged before
     - Process all files
     - Only re-tag files with existing tags but NOT AI-tagged
     - Do NOT re-tag any files that already have tags
   - **File Selection**:
     - Process all files in vault
     - Process files matching a pattern (e.g., `*.md`, `notes/*.md`)
     - Process selected files (user can choose from a list)
3. User clicks "Start Processing"
4. Progress modal appears showing:
   - Progress bar and percentage
   - Status (Processing, Completed, Failed)
   - List of files being processed with status
5. When complete, notification appears and dashboard refreshes

**Technical Notes**:
- Uses `/api/process-multiple-files` endpoint
- Task-based system with polling via `/api/task-status/{task_id}`
- AI suggestions come from Google Gemini API

### 2.3 Tag Aliases
**Purpose**: Create aliases for similar tags (e.g., map "js" and "javascript" to a canonical tag)

**User Flow**:
1. User navigates to "Tag Aliases" view
2. User generates aliases using:
   - **Heuristic Detection**: Uses predefined rules to find potential aliases
   - **AI-Powered Detection**: Uses AI to analyze and suggest aliases
3. Suggested aliases display with checkboxes (pre-selected)
4. User can unselect any alias they don't want
5. User clicks "Save Aliases" to save selections
6. Current aliases display in a separate section

**Technical Notes**:
- Aliases generated via `/api/generate-aliases`
- Saved via `/api/save-aliases`
- Current aliases loaded via `/api/get-aliases`

### 2.4 Tag Management (Rename, Merge, Delete)
**Purpose**: Perform bulk operations on tags across the vault

**User Flow**:
1. User navigates to one of the tag management views
2. For **Rename**:
   - User enters old tag and new tag
   - System replaces old tag with new tag in all files
3. For **Merge**:
   - User enters multiple tags to merge and a new tag name
   - System replaces all instances of old tags with new tag
4. For **Delete**:
   - User enters tags to delete
   - System removes specified tags from all files
5. After operation, notification appears

**Technical Notes**:
- These features are currently placeholder views in the UI
- Backend functions exist but need UI implementation

### 2.5 Validate Tags
**Purpose**: Check vault for tag issues (malformed, duplicates, orphans)

**User Flow**:
1. User navigates to "Validate Tags" view
2. User clicks "Validate All Tags"
3. System checks all tags and displays report:
   - Total tags
   - Malformed tags (with spaces, periods, uppercase)
   - Duplicate tag groups (case-insensitive duplicates)
   - Orphaned tags (used in only 1 file)
4. Each section lists problematic tags

**Technical Notes**:
- Validation done via `/api/validate-tags`
- Results categorized by issue type

### 2.6 Settings
**Purpose**: Configure app behavior

**User Flow**:
1. User navigates to "Settings" view
2. User can see and update:
   - Vault path (read-only, with copy button)
   - AI prompt (customizable text for AI suggestions)
   - Excluded tags (tags to skip during processing)
   - Excluded paths (folders to skip during processing)
3. User can add/remove excluded tags and paths
4. User can update AI prompt
5. User can update tag database (rescan vault)

**Technical Notes**:
- Settings loaded via `/api/status`, `/api/config`, `/api/ai-prompt`
- Updates via `/api/update-config` and `/api/update-ai-prompt`
- Tag database update via `/api/update-tag-database`

## 3. User Interactions & Feedback

### 3.1 Navigation
- Sidebar navigation with links to all main views
- Active view highlighted
- Keyboard shortcuts (Ctrl+R for refresh, Ctrl+1/2/3 for views)

### 3.2 Notifications
- Toast notifications for:
  - Success (e.g., "Files processed successfully")
  - Errors (e.g., "Failed to process files")
  - Information (e.g., "Dashboard refreshed")
- Auto-dismiss after a few seconds

### 3.3 Progress Indicators
- Progress modals for long-running operations
- Show percentage, status, and detailed file list
- Can be closed manually or auto-close when complete

### 3.4 Loading States
- Loading spinners for data being fetched
- Placeholder content while loading
- Error states with retry options

## 4. Technical Architecture

### 4.1 Frontend-Backend Communication
- RESTful API with JSON responses
- Key endpoints:
  - `/api/status` - Vault status and statistics
  - `/api/files` - List of files in vault
  - `/api/tags` - All tags in vault
  - `/api/process-multiple-files` - Start processing files
  - `/api/task-status/{task_id}` - Check task progress
  - `/api/generate-aliases` - Create tag aliases
  - `/api/validate-tags` - Check tag issues
  - `/api/config` - Get/set configuration

### 4.2 Data Flow
1. User interacts with UI
2. JavaScript makes API call to Flask backend
3. Backend uses core module (`automator_core.py`) to perform operations
4. Core module uses:
   - `tag_processor.py` for file I/O and tag processing
   - `ai_integration.py` for AI suggestions
   - `config_manager.py` for configuration
5. Results returned to UI for display

### 4.3 File Processing Workflow
1. User selects files and options
2. System checks if files should be skipped (based on options and exclusions)
3. For each file:
   - Extract front matter and content
   - Get existing tags
   - Request AI suggestions based on content
   - Combine existing and suggested tags
   - Apply aliases and clean tags
   - Write updated tags back to file
4. Track progress and report results

## 5. Design Considerations

### 5.1 Responsive Design
- Should work on desktop and tablet
- Sidebar navigation that collapses on smaller screens
- Cards and tables that adapt to screen size

### 5.2 Accessibility
- Proper contrast ratios for dark theme
- Keyboard navigation support
- Screen reader compatibility
- Clear error messages

### 5.3 Performance
- Efficient loading of large file lists
- Caching of tag data
- Progressive loading for large vaults
- Background processing with status updates

### 5.4 Visual Hierarchy
- Clear distinction between primary and secondary actions
- Grouping of related controls
- Consistent use of color for status indicators
- Appropriate spacing and typography

## 6. Current UI Structure (For Reference)

### 6.1 Layout
- Fixed sidebar navigation on the left
- Main content area on the right
- Dashboard shows multiple cards with statistics and recent activity

### 6.2 Components
- Glass-effect cards for sections
- Tables for file lists
- Progress bars and modals for operations
- Forms for settings and inputs
- Toast notifications

### 6.3 Styling
- Dark theme with blue accents
- Tailwind CSS for styling
- Icons from Font Awesome
- Subtle animations and transitions

## 7. Future Enhancements to Consider

### 7.1 Visual Improvements
- Tag cloud visualization
- Graph view of tag relationships
- Timeline view of tag additions
- Before/after comparison for processed files

### 7.2 Functionality Enhancements
- Batch tag operations with preview
- Tag hierarchy support (nested tags)
- Integration with Obsidian plugins
- Export/import tag configurations

### 7.3 UX Improvements
- Guided onboarding for new users
- Contextual help and tooltips
- Advanced search and filtering
- Undo/redo functionality

This documentation provides a comprehensive overview of the Obsidian Tag Automator's functionality and user flows. Designers can use this to create an intuitive, efficient interface that meets users' needs while maintaining the app's powerful functionality.