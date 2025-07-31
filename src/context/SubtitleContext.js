import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { subtitleService } from '../services/subtitleService';

// Initial state
const initialState = {
  videoFile: null,
  subtitles: [],
  srtContent: '',
  isProcessing: false,
  progress: 0,
  processing: {
    currentStep: '',
    message: '',
    completed: false,
    error: null
  },
  fontSettings: {
    family: 'Inter',
    size: 16,
    color: '#ffffff',
    backgroundColor: '#000000',
    bold: false,
    italic: false,
    underline: false,
    shadow: true
  },
  selectedLanguage: 'auto',
  modelName: 'base',
  outputPath: null,
  error: null
};

// Action types
const actionTypes = {
  SET_VIDEO_FILE: 'SET_VIDEO_FILE',
  SET_SUBTITLES: 'SET_SUBTITLES',
  SET_SRT_CONTENT: 'SET_SRT_CONTENT',
  SET_PROCESSING: 'SET_PROCESSING',
  SET_PROGRESS: 'SET_PROGRESS',
  UPDATE_PROCESSING: 'UPDATE_PROCESSING',
  UPDATE_FONT_SETTINGS: 'UPDATE_FONT_SETTINGS',
  SET_LANGUAGE: 'SET_LANGUAGE',
  SET_MODEL: 'SET_MODEL',
  SET_OUTPUT_PATH: 'SET_OUTPUT_PATH',
  SET_ERROR: 'SET_ERROR',
  RESET_STATE: 'RESET_STATE'
};

// Reducer
const subtitleReducer = (state, action) => {
  switch (action.type) {
    case actionTypes.SET_VIDEO_FILE:
      return {
        ...state,
        videoFile: action.payload,
        subtitles: [],
        srtContent: '',
        error: null
      };

    case actionTypes.SET_SUBTITLES:
      return {
        ...state,
        subtitles: action.payload
      };

    case actionTypes.SET_SRT_CONTENT:
      return {
        ...state,
        srtContent: action.payload
      };

    case actionTypes.SET_PROCESSING:
      return {
        ...state,
        isProcessing: action.payload
      };

    case actionTypes.SET_PROGRESS:
      return {
        ...state,
        progress: action.payload
      };

    case actionTypes.UPDATE_PROCESSING:
      return {
        ...state,
        processing: {
          ...state.processing,
          ...action.payload
        }
      };

    case actionTypes.UPDATE_FONT_SETTINGS:
      return {
        ...state,
        fontSettings: {
          ...state.fontSettings,
          ...action.payload
        }
      };

    case actionTypes.SET_LANGUAGE:
      return {
        ...state,
        selectedLanguage: action.payload
      };

    case actionTypes.SET_MODEL:
      return {
        ...state,
        modelName: action.payload
      };

    case actionTypes.SET_OUTPUT_PATH:
      return {
        ...state,
        outputPath: action.payload
      };

    case actionTypes.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        isProcessing: false
      };

    case actionTypes.RESET_STATE:
      return initialState;

    default:
      return state;
  }
};

// Create context
const SubtitleContext = createContext();

// Provider component
export const SubtitleProvider = ({ children }) => {
  const [state, dispatch] = useReducer(subtitleReducer, initialState);

  // Helper function to parse SRT content into subtitle objects
  const parseSRTContent = useCallback((srtContent) => {
    const subtitles = [];
    const blocks = srtContent.trim().split('\n\n');
    
    blocks.forEach((block) => {
      const lines = block.trim().split('\n');
      if (lines.length >= 3) {
        const id = parseInt(lines[0]);
        const timeMatch = lines[1].match(/(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})/);
        
        if (timeMatch) {
          const startTime = timeMatch[1];
          const endTime = timeMatch[2];
          const text = lines.slice(2).join('\n');
          
          subtitles.push({
            id,
            startTime,
            endTime,
            text: text.trim()
          });
        }
      }
    });
    
    return subtitles;
  }, []);

  // Action creators
  const setVideoFile = useCallback((file) => {
    dispatch({ type: actionTypes.SET_VIDEO_FILE, payload: file });
  }, []);

  const setSubtitles = useCallback((subtitles) => {
    dispatch({ type: actionTypes.SET_SUBTITLES, payload: subtitles });
  }, []);

  const setSRTContent = useCallback((content) => {
    dispatch({ type: actionTypes.SET_SRT_CONTENT, payload: content });
    const parsedSubtitles = parseSRTContent(content);
    dispatch({ type: actionTypes.SET_SUBTITLES, payload: parsedSubtitles });
  }, [parseSRTContent]);

  const updateFontSettings = useCallback((updates) => {
    dispatch({ type: actionTypes.UPDATE_FONT_SETTINGS, payload: updates });
  }, []);

  const setSelectedLanguage = useCallback((language) => {
    dispatch({ type: actionTypes.SET_LANGUAGE, payload: language });
  }, []);

  const setModelName = useCallback((model) => {
    dispatch({ type: actionTypes.SET_MODEL, payload: model });
  }, []);

  const setError = useCallback((error) => {
    dispatch({ type: actionTypes.SET_ERROR, payload: error });
  }, []);

  // Process video function
  const processVideo = useCallback(async (videoFile) => {
    if (!videoFile) return;

    dispatch({ type: actionTypes.SET_PROCESSING, payload: true });
    dispatch({ type: actionTypes.SET_PROGRESS, payload: 0 });
    dispatch({ type: actionTypes.UPDATE_PROCESSING, payload: {
      currentStep: 'Initializing...',
      message: 'Preparing to process video',
      completed: false,
      error: null
    }});

    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('video', videoFile);
      formData.append('language', state.selectedLanguage);
      formData.append('model', state.modelName);
      formData.append('create_video', 'true');
      
      // Add font settings
      formData.append('font_family', state.fontSettings.family);
      formData.append('font_size', state.fontSettings.size.toString());
      formData.append('font_color', state.fontSettings.color);
      formData.append('outline_color', state.fontSettings.backgroundColor);
      formData.append('bold', state.fontSettings.bold.toString());
      formData.append('italic', state.fontSettings.italic.toString());
      formData.append('shadow', state.fontSettings.shadow.toString());

      // Set up progress callback
      const onProgress = (step, message, progress = null) => {
        dispatch({ type: actionTypes.UPDATE_PROCESSING, payload: {
          currentStep: step,
          message: message
        }});
        
        if (progress !== null) {
          dispatch({ type: actionTypes.SET_PROGRESS, payload: progress });
        }
      };

      // Call the subtitle service
      const result = await subtitleService.processVideo(formData, onProgress);

      if (result.srtContent) {
        // Success - set the SRT content and parse subtitles
        setSRTContent(result.srtContent);
        dispatch({ type: actionTypes.SET_OUTPUT_PATH, payload: result.outputDir });
        dispatch({ type: actionTypes.UPDATE_PROCESSING, payload: {
          currentStep: 'Completed',
          message: 'Video processing completed successfully!',
          completed: true,
          error: null
        }});
        dispatch({ type: actionTypes.SET_PROGRESS, payload: 100 });
      } else {
        throw new Error(result.message || 'Failed to process video');
      }
    } catch (error) {
      console.error('Video processing error:', error);
      dispatch({ type: actionTypes.UPDATE_PROCESSING, payload: {
        currentStep: 'Error',
        message: error.message || 'An error occurred during processing',
        completed: false,
        error: error.message
      }});
      setError(error.message);
    } finally {
      dispatch({ type: actionTypes.SET_PROCESSING, payload: false });
    }
  }, [state.selectedLanguage, state.modelName, state.fontSettings, setSRTContent, setError]);

  // Update subtitle text
  const updateSubtitleText = useCallback((id, newText) => {
    const updatedSubtitles = state.subtitles.map(subtitle => 
      subtitle.id === id ? { ...subtitle, text: newText } : subtitle
    );
    dispatch({ type: actionTypes.SET_SUBTITLES, payload: updatedSubtitles });
  }, [state.subtitles]);

  // Export SRT
  const exportSRT = useCallback(() => {
    let srtContent = '';
    state.subtitles.forEach((subtitle) => {
      srtContent += `${subtitle.id}\n`;
      srtContent += `${subtitle.startTime} --> ${subtitle.endTime}\n`;
      srtContent += `${subtitle.text}\n\n`;
    });
    return srtContent;
  }, [state.subtitles]);

  // Reset state
  const resetState = useCallback(() => {
    dispatch({ type: actionTypes.RESET_STATE });
  }, []);

  const value = {
    // State
    ...state,
    
    // Actions
    setVideoFile,
    setSubtitles,
    setSRTContent,
    updateFontSettings,
    setSelectedLanguage,
    setModelName,
    setError,
    processVideo,
    updateSubtitleText,
    exportSRT,
    resetState
  };

  return (
    <SubtitleContext.Provider value={value}>
      {children}
    </SubtitleContext.Provider>
  );
};

// Custom hook
export const useSubtitle = () => {
  const context = useContext(SubtitleContext);
  if (!context) {
    throw new Error('useSubtitle must be used within a SubtitleProvider');
  }
  return context;
};
