import React from 'react';
import { Type, Bold, Italic, Underline, Palette } from 'lucide-react';
import './FontStylePanel.css';

const FontStylePanel = ({ fontSettings, onFontChange }) => {
  const fontFamilies = [
    { value: 'Inter', label: 'Inter' },
    { value: 'Arial', label: 'Arial' },
    { value: 'Helvetica', label: 'Helvetica' },
    { value: 'Georgia', label: 'Georgia' },
    { value: 'Times New Roman', label: 'Times New Roman' },
    { value: 'Courier New', label: 'Courier New' },
    { value: 'Verdana', label: 'Verdana' },
    { value: 'Roboto', label: 'Roboto' }
  ];

  const handleFontFamilyChange = (e) => {
    onFontChange({ family: e.target.value });
  };

  const handleSizeChange = (e) => {
    onFontChange({ size: parseInt(e.target.value) });
  };

  const handleColorChange = (e) => {
    onFontChange({ color: e.target.value });
  };

  const handleBackgroundColorChange = (e) => {
    onFontChange({ backgroundColor: e.target.value });
  };

  const toggleStyle = (style) => {
    onFontChange({ [style]: !fontSettings[style] });
  };

  const toggleShadow = () => {
    onFontChange({ shadow: !fontSettings.shadow });
  };

  return (
    <div className="font-style-panel">
      <div className="panel-header">
        <Type size={20} />
        <h3>Font Style</h3>
      </div>

      <div className="panel-content">
        {/* Font Family */}
        <div className="control-group">
          <label>Font Family</label>
          <select 
            value={fontSettings.family} 
            onChange={handleFontFamilyChange}
            className="font-select"
          >
            {fontFamilies.map(font => (
              <option key={font.value} value={font.value}>
                {font.label}
              </option>
            ))}
          </select>
        </div>

        {/* Font Size */}
        <div className="control-group">
          <label>Size: {fontSettings.size}px</label>
          <input 
            type="range"
            min="12"
            max="48"
            value={fontSettings.size}
            onChange={handleSizeChange}
            className="size-slider"
          />
        </div>

        {/* Text Color */}
        <div className="control-group">
          <label>Text Color</label>
          <div className="color-input-group">
            <input 
              type="color"
              value={fontSettings.color}
              onChange={handleColorChange}
              className="color-input"
            />
            <span className="color-value">{fontSettings.color}</span>
          </div>
        </div>

        {/* Background Color */}
        <div className="control-group">
          <label>Background</label>
          <div className="color-input-group">
            <input 
              type="color"
              value={fontSettings.backgroundColor}
              onChange={handleBackgroundColorChange}
              className="color-input"
            />
            <span className="color-value">{fontSettings.backgroundColor}</span>
          </div>
        </div>

        {/* Text Styles */}
        <div className="control-group">
          <label>Text Styles</label>
          <div className="style-toggles">
            <button 
              className={`style-toggle ${fontSettings.bold ? 'active' : ''}`}
              onClick={() => toggleStyle('bold')}
              title="Bold"
            >
              <Bold size={16} />
            </button>
            <button 
              className={`style-toggle ${fontSettings.italic ? 'active' : ''}`}
              onClick={() => toggleStyle('italic')}
              title="Italic"
            >
              <Italic size={16} />
            </button>
            <button 
              className={`style-toggle ${fontSettings.underline ? 'active' : ''}`}
              onClick={() => toggleStyle('underline')}
              title="Underline"
            >
              <Underline size={16} />
            </button>
          </div>
        </div>

        {/* Effects */}
        <div className="control-group">
          <label>Effects</label>
          <div className="effect-toggles">
            <label className="toggle-switch">
              <input 
                type="checkbox"
                checked={fontSettings.shadow}
                onChange={toggleShadow}
              />
              <span className="toggle-slider"></span>
              <span className="toggle-label">Text Shadow</span>
            </label>
          </div>
        </div>

        {/* Preview */}
        <div className="control-group">
          <label>Preview</label>
          <div className="font-preview">
            <div 
              className="preview-text"
              style={{
                fontFamily: fontSettings.family,
                fontSize: `${fontSettings.size}px`,
                color: fontSettings.color,
                backgroundColor: fontSettings.backgroundColor,
                fontWeight: fontSettings.bold ? 'bold' : 'normal',
                fontStyle: fontSettings.italic ? 'italic' : 'normal',
                textDecoration: fontSettings.underline ? 'underline' : 'none',
                textShadow: fontSettings.shadow ? '2px 2px 4px rgba(0,0,0,0.8)' : 'none',
                padding: '8px 12px',
                borderRadius: '4px',
                display: 'inline-block'
              }}
            >
              Sample subtitle text
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FontStylePanel;
