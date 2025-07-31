import React from 'react';
import { Loader } from 'lucide-react';
import './ProgressIndicator.css';

const ProgressIndicator = ({ progress, currentStep, isProcessing }) => {
  return (
    <div className="progress-indicator">
      {isProcessing ? (
        <>
          <div className="loader">
            <Loader size={24} />
          </div>
          <div className="progress-details">
            <p className="progress-status">{currentStep}</p>
            <div className="progress-bar">
              <div
                className="progress-bar-fill"
                style={{
                  width: `${progress}%`
                }}
              ></div>
            </div>
            <p className="progress-percentage">{progress}%</p>
          </div>
        </>
      ) : (
        <div className="complete-status">
          <p>Processing Complete</p>
        </div>
      )}
    </div>
  );
};

export default ProgressIndicator;
