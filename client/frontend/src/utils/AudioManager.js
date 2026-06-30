/**
 * AudioManager - Singleton for global audio control
 * Ensures only one audio plays at a time, like WhatsApp
 */
class AudioManager {
    constructor() {
        this.currentAudio = null;
        this.currentMessageId = null;
        this.listeners = new Map();
        this.isPlaying = false;
    }

    /**
     * Play an audio file
     * @param {string} audioUrl - URL of audio file
     * @param {string} messageId - Unique ID for this message
     * @returns {HTMLAudioElement} The audio element
     */
    play(audioUrl, messageId) {
        // Stop any currently playing audio
        this.stop();

        // Create and play new audio
        const audio = new Audio(audioUrl);
        audio.play().catch(err => {
            console.error('❌ Audio playback failed:', err);
        });
        
        this.currentAudio = audio;
        this.currentMessageId = messageId;
        this.isPlaying = true;

        // Notify listeners
        this.notifyListeners(messageId, 'play');

        // Auto-cleanup on end
        audio.onended = () => {
            this.stop();
        };

        // Cleanup on error
        audio.onerror = () => {
            this.stop();
        };

        return audio;
    }

    /**
     * Stop currently playing audio
     */
    stop() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            const oldId = this.currentMessageId;
            this.currentAudio = null;
            this.currentMessageId = null;
            this.isPlaying = false;
            this.notifyListeners(oldId, 'stop');
        }
    }

    /**
     * Toggle play/pause for an audio
     */
    toggle(audioUrl, messageId) {
        if (this.currentMessageId === messageId && this.currentAudio) {
            if (this.currentAudio.paused) {
                this.currentAudio.play();
                this.isPlaying = true;
                this.notifyListeners(messageId, 'play');
            } else {
                this.currentAudio.pause();
                this.isPlaying = false;
                this.notifyListeners(messageId, 'pause');
            }
        } else {
            this.play(audioUrl, messageId);
        }
    }

    /**
     * Check if a specific audio is playing
     */
    isPlayingMessage(messageId) {
        return this.currentMessageId === messageId && 
               this.isPlaying &&
               this.currentAudio && 
               !this.currentAudio.paused;
    }

    /**
     * Get current playback progress (0-100)
     */
    getProgress() {
        if (this.currentAudio && this.currentAudio.duration) {
            return (this.currentAudio.currentTime / this.currentAudio.duration) * 100;
        }
        return 0;
    }

    /**
     * Get current duration in seconds
     */
    getDuration() {
        if (this.currentAudio && this.currentAudio.duration) {
            return this.currentAudio.duration;
        }
        return 0;
    }

    /**
     * Add listener for audio events
     */
    addListener(messageId, callback) {
        if (!this.listeners.has(messageId)) {
            this.listeners.set(messageId, []);
        }
        this.listeners.get(messageId).push(callback);
    }

    /**
     * Remove listener
     */
    removeListener(messageId, callback) {
        const callbacks = this.listeners.get(messageId) || [];
        this.listeners.set(
            messageId,
            callbacks.filter(cb => cb !== callback)
        );
    }

    /**
     * Notify all listeners of an event
     */
    notifyListeners(messageId, event) {
        const callbacks = this.listeners.get(messageId) || [];
        callbacks.forEach(cb => cb(event));
    }
}

// Export singleton instance
const audioManager = new AudioManager();
export default audioManager;
