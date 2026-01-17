# RAG Search Engine UI

A modern, beautiful web interface for the RAG Search Engine with drag-and-drop upload, intelligent Q&A, and conversation tracking.

## 🎨 Features

- **📤 Drag & Drop Upload** - Intuitive file upload with visual feedback
- **💬 Smart Q&A Interface** - Chat-like interface with source citations
- **📚 Document Manager** - View and delete uploaded documents
- **🕒 Chat History** - Track all conversations with timestamps
- **✨ Premium Design** - Dark theme with glassmorphism and smooth animations

## 🚀 Getting Started

### Prerequisites

Make sure the backend server is running:

```bash
# From the project root directory
uvicorn main:app --reload
```

The server should be running at `http://127.0.0.1:8000`

### Running the UI

1. **Navigate to the UI folder:**
   ```bash
   cd ui
   ```

2. **Open in browser:**
   - Simply open `index.html` in your browser
   - Or use a local server:
     ```bash
     # Using Python
     python -m http.server 8080
     
     # Then open http://localhost:8080
     ```

3. **Start using:**
   - Upload PDFs via drag-and-drop or file browser
   - Ask questions about your documents
   - View source citations for each answer
   - Manage your documents in the sidebar

## 🎨 Design System

### Color Palette
- **Primary Gradient**: Cyan (#00d4ff) → Purple (#a855f7)
- **Background**: Dark theme with animated gradients
- **Surface**: Glassmorphic cards with backdrop blur

### Typography
- **Font**: Inter (Google Fonts)
- **Sizes**: Scales from 0.75rem to 2rem

### Effects
- Smooth animations and transitions
- Hover effects on interactive elements
- Loading states and progress indicators
- Toast notifications for user feedback

## 📁 File Structure

```
ui/
├── index.html          # Main HTML structure
├── style.css           # Design system and styles
├── script.js           # JavaScript functionality
└── README.md           # This file
```

## 🔧 Configuration

To change the API endpoint, edit the `API_BASE_URL` in `script.js`:

```javascript
const API_BASE_URL = 'http://127.0.0.1:8000';
```

## 📱 Responsive Design

The UI is fully responsive and works on:
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (< 768px)

## 🎯 API Integration

The UI integrates with these backend endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/upload` | POST | Upload PDF files |
| `/ask` | POST | Ask questions |
| `/documents` | GET | List all documents |
| `/documents/{id}` | DELETE | Delete specific document |
| `/history` | GET | Get chat history |
| `/clear-history` | DELETE | Clear all history |

## 💡 Usage Tips

1. **Upload Multiple Files**: Select or drag multiple PDFs at once
2. **Quick Questions**: Press Enter to submit questions
3. **Source Citations**: Click on sources to see where answers came from
4. **History Management**: Use the clear button to reset conversation history
5. **Document Management**: Delete individual documents when no longer needed

## 🎨 Customization

### Change Theme Colors

Edit the CSS variables in `style.css`:

```css
:root {
    --color-accent-cyan: #00d4ff;
    --color-accent-purple: #a855f7;
    /* Add your custom colors */
}
```

### Modify Chat Appearance

Adjust message styles in the `.message-question` and `.message-answer` classes.

### Update Animations

Modify the `@keyframes` rules for different animation effects.

## 🐛 Troubleshooting

### CORS Issues
If you encounter CORS errors, ensure the backend is configured to allow requests from your frontend origin. The FastAPI backend should already have CORS middleware enabled.

### API Connection Failed
- Verify the backend server is running
- Check the `API_BASE_URL` in `script.js`
- Ensure no firewall is blocking the connection

### Files Not Uploading
- Confirm files are PDFs
- Check file size limits
- Verify upload permissions

## 📄 License

This UI is part of the RAG Search Engine project and follows the same MIT License.

---

<div align="center">
Made with ❤️ using HTML, CSS, and Vanilla JavaScript
</div>
