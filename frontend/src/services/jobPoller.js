/**
 * Job Poller Service
 * Handles polling background job status from backend
 * 
 * Used for long-running operations like:
 * - CSV imports
 * - Recategorization
 * - Transfer detection
 * - Recurring transaction detection
 * 
 * Audit reference: 09_frontend_action_plan.md - P0 CSV import async
 */

import api from './api';

/**
 * Job status enum
 */
export const JobStatus = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
};

/**
 * Default polling configuration
 */
const DEFAULT_CONFIG = {
  initialInterval: 500,      // Start polling every 500ms
  maxInterval: 5000,          // Max polling interval of 5s
  backoffMultiplier: 1.5,     // Increase interval by 1.5x each time
  timeout: 300000,            // 5 minutes timeout
  maxRetries: 3               // Max consecutive failures before giving up
};

/**
 * Get job status from backend
 * 
 * @param {string|number} jobId - Job ID to check
 * @returns {Promise<Object>} Job status object
 */
export async function getJobStatus(jobId) {
  const response = await api.get(`/jobs/${jobId}`);
  return response.data;
}

/**
 * Wait for job to complete with simple polling
 * 
 * @param {string|number} jobId - Job ID to wait for
 * @param {Object} config - Polling configuration
 * @returns {Promise<Object>} Final job status
 * @throws {Error} If job fails or times out
 */
export async function waitForJob(jobId, config = {}) {
  const cfg = { ...DEFAULT_CONFIG, ...config };
  
  let interval = cfg.initialInterval;
  let elapsed = 0;
  let consecutiveFailures = 0;
  
  while (elapsed < cfg.timeout) {
    try {
      const job = await getJobStatus(jobId);
      
      // Reset failure counter on success
      consecutiveFailures = 0;
      
      // Check terminal states
      if (job.status === JobStatus.COMPLETED) {
        return job;
      }
      
      if (job.status === JobStatus.FAILED) {
        throw new Error(job.error || 'Job failed');
      }
      
      if (job.status === JobStatus.CANCELLED) {
        throw new Error('Job was cancelled');
      }
      
      // Still running or pending - wait and retry
      await sleep(interval);
      elapsed += interval;
      
      // Exponential backoff
      interval = Math.min(interval * cfg.backoffMultiplier, cfg.maxInterval);
      
    } catch (error) {
      consecutiveFailures++;
      
      // If we've failed too many times, give up
      if (consecutiveFailures >= cfg.maxRetries) {
        throw new Error(`Failed to poll job after ${cfg.maxRetries} attempts: ${error.message}`);
      }
      
      // Wait a bit before retrying
      await sleep(interval);
      elapsed += interval;
    }
  }
  
  throw new Error(`Job timed out after ${cfg.timeout}ms`);
}

/**
 * Start polling a job with progress callbacks
 * Returns a controller object to manage polling
 * 
 * @param {string|number} jobId - Job ID to poll
 * @param {Object} callbacks - Callback functions
 * @param {Function} callbacks.onUpdate - Called on each status update
 * @param {Function} callbacks.onComplete - Called when job completes
 * @param {Function} callbacks.onError - Called on error or failure
 * @param {Object} config - Polling configuration
 * @returns {Object} Controller with stop() method
 */
export function startPolling(jobId, callbacks = {}, config = {}) {
  const { onUpdate, onComplete, onError } = callbacks;
  const cfg = { ...DEFAULT_CONFIG, ...config };
  
  let interval = cfg.initialInterval;
  let elapsed = 0;
  let consecutiveFailures = 0;
  let stopped = false;
  let timeoutId = null;
  
  /**
   * Single poll iteration
   */
  const poll = async () => {
    if (stopped) return;
    
    try {
      const job = await getJobStatus(jobId);
      
      // Reset failure counter
      consecutiveFailures = 0;
      
      // Notify update callback
      if (onUpdate) {
        try {
          onUpdate(job);
        } catch (err) {
          console.error('Error in onUpdate callback:', err);
        }
      }
      
      // Check terminal states
      if (job.status === JobStatus.COMPLETED) {
        if (onComplete) {
          try {
            onComplete(job);
          } catch (err) {
            console.error('Error in onComplete callback:', err);
          }
        }
        return; // Stop polling
      }
      
      if (job.status === JobStatus.FAILED) {
        const error = new Error(job.error || 'Job failed');
        if (onError) {
          try {
            onError(error, job);
          } catch (err) {
            console.error('Error in onError callback:', err);
          }
        }
        return; // Stop polling
      }
      
      if (job.status === JobStatus.CANCELLED) {
        const error = new Error('Job was cancelled');
        if (onError) {
          try {
            onError(error, job);
          } catch (err) {
            console.error('Error in onError callback:', err);
          }
        }
        return; // Stop polling
      }
      
      // Continue polling
      elapsed += interval;
      
      // Check timeout
      if (elapsed >= cfg.timeout) {
        const error = new Error(`Job timed out after ${cfg.timeout}ms`);
        if (onError) {
          try {
            onError(error, job);
          } catch (err) {
            console.error('Error in onError callback:', err);
          }
        }
        return;
      }
      
      // Exponential backoff
      interval = Math.min(interval * cfg.backoffMultiplier, cfg.maxInterval);
      
      // Schedule next poll
      timeoutId = setTimeout(poll, interval);
      
    } catch (error) {
      consecutiveFailures++;
      
      // If we've failed too many times, give up
      if (consecutiveFailures >= cfg.maxRetries) {
        const err = new Error(`Failed to poll job after ${cfg.maxRetries} attempts: ${error.message}`);
        if (onError) {
          try {
            onError(err);
          } catch (cbErr) {
            console.error('Error in onError callback:', cbErr);
          }
        }
        return;
      }
      
      // Retry after interval
      elapsed += interval;
      timeoutId = setTimeout(poll, interval);
    }
  };
  
  // Start polling
  poll();
  
  // Return controller
  return {
    /**
     * Stop polling
     */
    stop: () => {
      stopped = true;
      if (timeoutId !== null) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
    },
    
    /**
     * Check if polling is active
     */
    isActive: () => !stopped
  };
}

/**
 * Helper to sleep for specified milliseconds
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Cancel a job
 * 
 * @param {string|number} jobId - Job ID to cancel
 * @returns {Promise<Object>} Cancellation response
 */
export async function cancelJob(jobId) {
  const response = await api.post(`/jobs/${jobId}/cancel`);
  return response.data;
}
