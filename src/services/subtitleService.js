import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

export const subtitleService = {
  async processVideo(formData, onProgress) {
    try {
      // Step 1: Start the processing job
      if (onProgress) {
        onProgress('Uploading...', 'Uploading video to server', 5);
      }

      const response = await axios.post(`${API_BASE_URL}/process-video`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 30000 // 30 second timeout for upload
      });

      const { job_id } = response.data;
      
      if (onProgress) {
        onProgress('Processing...', 'Video uploaded successfully, starting processing', 10);
      }

      // Step 2: Poll for job status
      return await this.pollJobStatus(job_id, onProgress);

    } catch (error) {
      console.error('Failed to process video:', error);
      if (error.response) {
        // Server responded with error status
        const errorMessage = error.response.data?.error || error.response.statusText;
        throw new Error(`Server error: ${errorMessage}`);
      } else if (error.request) {
        // Request was made but no response received
        throw new Error('Cannot connect to server. Please make sure the backend is running.');
      } else {
        // Something else happened
        throw new Error(`Request failed: ${error.message}`);
      }
    }
  },

  async pollJobStatus(jobId, onProgress) {
    const maxAttempts = 300; // 5 minutes with 1-second intervals
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const response = await axios.get(`${API_BASE_URL}/job-status/${jobId}`);
        const data = response.data;

        if (data.type === 'complete') {
          // Job completed successfully
          if (onProgress) {
            onProgress('Complete', 'Processing completed successfully!', 100);
          }
          return data;
        } else if (data.type === 'error') {
          // Job failed
          throw new Error(data.error || 'Processing failed');
        } else {
          // Job still in progress
          if (onProgress) {
            onProgress(
              data.current_step || 'Processing',
              data.message || 'Processing video...',
              data.progress || 0
            );
          }
        }

        // Wait before next poll
        await new Promise(resolve => setTimeout(resolve, 1000));
        attempts++;

      } catch (error) {
        if (error.response?.status === 404) {
          throw new Error('Job not found on server');
        }
        console.error('Error polling job status:', error);
        attempts++;
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait longer on error
      }
    }

    throw new Error('Processing timeout. Please try again.');
  },

  async checkServerHealth() {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`, {
        timeout: 5000
      });
      return response.data;
    } catch (error) {
      throw new Error('Server is not responding');
    }
  }
};

