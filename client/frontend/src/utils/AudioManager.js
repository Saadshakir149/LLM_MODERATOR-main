/**
 * AudioManager - Singleton for global audio control
 * Ensures only ONE audio plays at a time
 */
class AudioManager {
    constructor() {
        this.currentAudio = null;
        this.currentMessageId = null;
        this.isPlaying = false;
        this.listeners = new Map();
        this.onPlayCallbacks = [];
        console.log('🎵 AudioManager initialized');
    }

    /**
     * Play an audio file
     * @param {string} audioUrl - URL of audio file
     * @param {string} messageId - Unique ID for this message
     * @returns {HTMLAudioElement} The audio element
     */
    play(audioUrl, messageId) {
        console.log(`▶️ Playing: ${messageId}`);
        
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
        this._notifyListeners(messageId, 'play');
        this._notifyPlayCallbacks(audioUrl, messageId);

        // Auto-cleanup on end
        audio.onended = () => {
            console.log(`⏹️ Audio ended: ${messageId}`);
            this.stop();
        };

        // Cleanup on error
        audio.onerror = (err) => {
            console.error(`❌ Audio error: ${messageId}`, err);
            this.stop();
        };

        return audio;
    }

    /**
     * Stop currently playing audio
     */
    stop() {
        if (this.currentAudio) {
            console.log(`⏹️ Stopping: ${this.currentMessageId}`);
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            const oldId = this.currentMessageId;
            this.currentAudio = null;
            this.currentMessageId = null;
            this.isPlaying = false;
            this._notifyListeners(oldId, 'stop');
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
                this._notifyListeners(messageId, 'play');
            } else {
                this.currentAudio.pause();
                this.isPlaying = false;
                this._notifyListeners(messageId, 'pause');
            }
        } else {
            this.play(audioUrl, messageId);
        }
    }

    /**
     * Register callback for when ANY audio starts
     */
    registerOnPlayCallback(callback) {
        if (typeof callback === 'function') {
            this.onPlayCallbacks.push(callback);
            console.log('✅ Play callback registered, total:', this.onPlayCallbacks.length);
        } else {
            console.warn('⚠️ registerOnPlayCallback: Not a function');
        }
    }

    /**
     * Unregister play callback
     */
    unregisterOnPlayCallback(callback) {
        this.onPlayCallbacks = this.onPlayCallbacks.filter(cb => cb !== callback);
        console.log('❌ Play callback unregistered, remaining:', this.onPlayCallbacks.length);
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
     * Add listener for specific audio
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
    _notifyListeners(messageId, event) {
        const callbacks = this.listeners.get(messageId) || [];
        callbacks.forEach(cb => {
            try {
                cb(event);
            } catch (err) {
                console.error('❌ Listener error:', err);
            }
        });
    }

    /**
     * Notify play callbacks when ANY audio starts playing
     */
    _notifyPlayCallbacks(audioUrl, messageId) {
        console.log(`📢 Notifying ${this.onPlayCallbacks.length} play callbacks`);
        this.onPlayCallbacks.forEach(cb => {
            try {
                cb(audioUrl, messageId);
            } catch (err) {
                console.error('❌ Play callback error:', err);
            }
        });
    }
}

// Create and export singleton instance
const audioManager = new AudioManager();
export default audioManager;
