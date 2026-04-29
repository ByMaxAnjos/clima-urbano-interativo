"""
Glass Morphism Components Examples
===================================

This module demonstrates how to use the new glassmorphic components
from style-enhanced.css in your Streamlit application.

Each component is shown with light mode and dark mode previews.
"""

import streamlit as st

# Set page config
st.set_page_config(
    page_title="Glassmorphism Components",
    page_icon="🎨",
    layout="wide"
)

st.title("🎨 Glass Morphism Components Demo")

st.markdown("""
This page showcases the new glassmorphic components available in **style-enhanced.css**.
Components automatically adapt to light and dark modes based on system preference.
""")

# ============================================================
# Glass Card Component
# ============================================================
st.header("1. Glass Card")
st.markdown("""
The `.glass-card` class creates a frosted glass effect panel with subtle borders
and intelligent shadows. Perfect for highlighting key information.
""")

st.markdown("""
<div class="glass-card">
    <h3 style="color: var(--primary-dark); margin-top: 0;">Climate Analysis Card</h3>
    <p>This is a glass-effect card demonstrating the modern frosted glass aesthetic.</p>
    <p style="color: var(--text-muted); font-size: 0.9em;">
        Uses backdrop-filter: blur(16px) with intelligent border and shadow treatment.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
<div class="glass-card">
    <h4 style="color: var(--primary-dark); margin-top: 0;">Urban Temperature</h4>
    <p>32°C</p>
    <p style="color: var(--text-muted);">Downtown area</p>
</div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
<div class="glass-card">
    <h4 style="color: var(--primary-dark); margin-top: 0;">Green Coverage</h4>
    <p>45%</p>
    <p style="color: var(--text-muted);">Park & vegetation</p>
</div>
    """, unsafe_allow_html=True)

# ============================================================
# Glass Panel Component
# ============================================================
st.header("2. Glass Panel")
st.markdown("""
The `.glass-panel` class creates a larger frosted glass container ideal for
major sections and complex layouts.
""")

st.markdown("""
<div class="glass-panel">
    <h3 style="color: var(--text-primary); margin-top: 0;">Advanced Urban Climate Analysis</h3>
    <p>
        Large panels with enhanced blur effect (24px) and stronger shadows for
        visual separation. Perfect for detailed analysis sections or complex data presentations.
    </p>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div style="padding: 1rem; background: rgba(16, 185, 129, 0.1); border-radius: 8px;">
            <strong>Temperature Gradient</strong>
            <p style="margin: 0.5rem 0 0 0; color: var(--text-muted);">
                Heat island intensity increases 3-5°C in urban cores
            </p>
        </div>
        <div style="padding: 1rem; background: rgba(14, 165, 233, 0.1); border-radius: 8px;">
            <strong>Vegetation Impact</strong>
            <p style="margin: 0.5rem 0 0 0; color: var(--text-muted);">
                Green areas reduce local temperature by 2-4°C
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Glass Button Component
# ============================================================
st.header("3. Glass Button")
st.markdown("""
The `.glass-button` class provides an elegant glass-effect button style.
These buttons work well in custom HTML for interactive elements.
""")

st.markdown("""
<div style="display: flex; gap: 1rem; flex-wrap: wrap;">
    <button class="glass-button" onclick="alert('Glass button clicked!')">
        Analyze Area
    </button>
    <button class="glass-button" onclick="alert('Glass button clicked!')">
        Download Report
    </button>
    <button class="glass-button" onclick="alert('Glass button clicked!')">
        Compare Cities
    </button>
</div>
""", unsafe_allow_html=True)

st.info("Note: Native Streamlit buttons also have glassmorphic enhancements in style-enhanced.css")

# ============================================================
# Status Indicators
# ============================================================
st.header("4. Status Indicators with Glass Effect")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
<div class="status-indicator status-success">
    ✓ Analysis Complete
</div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
<div class="status-indicator status-info">
    ⓘ Data Processing
</div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
<div class="status-indicator status-warning">
    ⚠ High Temperature
</div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
<div class="status-indicator status-error">
    ✕ Data Missing
</div>
    """, unsafe_allow_html=True)

# ============================================================
# Animation Classes
# ============================================================
st.header("5. Micro-Animations")

st.markdown("""
The style-enhanced.css includes several reusable animation classes:

- **fade-in** — Fade in with slight vertical movement
- **fade-in-up** — Slide up while fading
- **slide-in-left** — Slide in from the left
- **glow-effect** — Continuous glowing effect
- **float-up** — Entrance with floating movement
- **pulse-hover** — Scale pulse on hover
""")

# Example of animations
st.markdown("""
<style>
    .animation-demo {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .demo-box {
        padding: 1.5rem;
        text-align: center;
        background: var(--surface-glass);
        border: 1px solid var(--border-glass);
        border-radius: var(--border-radius-lg);
    }
</style>

<div class="animation-demo">
    <div class="demo-box fade-in">
        <strong>fade-in</strong>
        <p style="color: var(--text-muted);">0.55s ease-out</p>
    </div>
    <div class="demo-box fade-in-up" style="animation-delay: 0.1s;">
        <strong>fade-in-up</strong>
        <p style="color: var(--text-muted);">0.60s ease-out</p>
    </div>
    <div class="demo-box slide-in-left" style="animation-delay: 0.2s;">
        <strong>slide-in-left</strong>
        <p style="color: var(--text-muted);">0.55s ease-out</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Responsive Behavior
# ============================================================
st.header("6. Responsive Design")

st.markdown("""
All glass components are fully responsive:
- **Desktop (>768px)**: Full size with generous spacing
- **Tablet (768px-480px)**: Adjusted padding and font sizes
- **Mobile (<480px)**: Optimized for small screens

Try resizing your browser to see the responsive behavior in action.
""")

# ============================================================
# Dark Mode Support
# ============================================================
st.header("7. Dark Mode Support")

st.markdown("""
All components automatically adapt to dark mode when:
- User's OS uses dark theme
- Browser CSS media `prefers-color-scheme: dark`
- Developer tools emulate dark mode

**To test dark mode:**
- macOS/Linux: System Settings → Appearance → Dark
- Windows: Settings → Personalization → Colors → Dark
- Browser DevTools: Cmd+Shift+P → "emulate CSS media feature"
""")

st.markdown("""
<div style="background: #0f1419; color: #e8f5e9; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
    <strong>Dark Mode Preview</strong>
    <p>This text demonstrates the dark mode color scheme applied automatically.</p>
    <div class="glass-card" style="background: rgba(26, 31, 38, 0.80); color: #e8f5e9;">
        <p>Glass card in dark mode</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# CSS Variables Available
# ============================================================
st.header("8. Available CSS Variables")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
**Colors**
- `--primary-color`: #10b981
- `--secondary-color`: #0ea5e9
- `--accent-color`: #c2410c
- `--surface-glass`: rgba(255,255,255,0.85)
- `--border-glass`: rgba(16,185,129,0.25)
    """)

with col2:
    st.markdown("""
**Effects**
- `--blur-sm`: blur(8px)
- `--blur-md`: blur(16px)
- `--blur-lg`: blur(24px)
- `--shadow-glass`: Multi-layer
- `--transition-smooth`: Bouncy easing
    """)

# ============================================================
# Implementation Guide
# ============================================================
st.header("9. Quick Implementation")

st.markdown("**To use in your Streamlit app:**")

st.code("""
import streamlit as st

# Use custom HTML with glass classes
st.markdown('''
<div class="glass-card">
    <h3>Your Content Here</h3>
    <p>Automatic glass effect applied</p>
</div>
''', unsafe_allow_html=True)

# Streamlit components automatically styled
st.button("Native button with glass effects")
st.metric("Label", "Value")
""", language="python")

# ============================================================
# Footer
# ============================================================
st.divider()
st.markdown("""
---
**Glassmorphism Theme Features:**
- Ultra-modern frosted glass aesthetic
- Automatic dark mode adaptation
- Micro-animations for polish
- Full accessibility support
- Zero breaking changes to existing code

📝 See `INTEGRATION_GUIDE.md` for detailed integration instructions.
""")
