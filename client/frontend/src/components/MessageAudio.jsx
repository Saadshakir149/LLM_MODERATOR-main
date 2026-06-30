import React, { useState, useEffect, useRef, useCallback } from 'react';
import audioManager from '../utils/AudioManager';

function MessageAudio({ audioUrl, messageId, timestamp }) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [progress, setProgress] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const progressInterval = useRef(null);
    const listenerRef = useRef(null);

    // Start progress tracking
    const startProgressTracking = useCallback(() => {
        if (progressInterval.current) return;
        progressInterval.current = setInterval(() => {
            const newProgress = audioManager.getProgress();
            const newDuration = audioManager.getDuration();
            setProgress(newProgress);
            if (newDuration > 0) {
                setDuration(newDuration);
                setIsLoading(false);
            }
        }, 100);
    }, []);

    // Stop progress tracking
    const stopProgressTracking = useCallback(() => {
        if (progressInterval.current) {
            clearInterval(progressInterval.current);
            progressInterval.current = null;
        }
    }, []);

    // Listen to global audio state
    useEffect(() => {
        const callback = (event) => {
            if (event === 'play') {
                setIsPlaying(true);
                startProgressTracking();
            } else if (event === 'stop' || event === 'pause') {
                setIsPlaying(false);
                stopProgressTracking();
            }
        };

        audioManager.addListener(messageId, callback);
        listenerRef.current = callback;

        // Check if this audio is already playing
        if (audioManager.isPlayingMessage(messageId)) {
            setIsPlaying(true);
            startProgressTracking();
        }

        return () => {
            audioManager.removeListener(messageId, callback);
            stopProgressTracking();
        };
    }, [messageId, startProgressTracking, stopProgressTracking]);

    // Handle play/pause
    const handlePlayPause = useCallback(() => {
        if (isPlaying) {
            // Pause current audio
            audioManager.stop();
        } else {
            // Play this audio (stops any other)
            audioManager.toggle(audioUrl, messageId);
        }
    }, [audioUrl, messageId, isPlaying]);

    // Format time (mm:ss)
    const formatTime = (seconds) => {
        if (!seconds || isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Handle progress bar click (seek)
    const handleProgressClick = (e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percentage = x / rect.width;
        const audio = audioManager.currentAudio;
        if (audio && audioManager.currentMessageId === messageId && audio.duration) {
            audio.currentTime = percentage * audio.duration;
            setProgress(percentage * 100);
        }
    };

    // Once audio is metadata-loaded, update the duration and loading state
    useEffect(() => {
        const audio = new Audio(audioUrl);
        const handleLoadedMetadata = () => {
            setDuration(audio.duration);
            setIsLoading(false);
        };
        audio.addEventListener('loadedmetadata', handleLoadedMetadata);
        // Fallback timeout in case loading fails or takes too long
        const timer = setTimeout(() => {
            setIsLoading(false);
        }, 3000);

        return () => {
            audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
            clearTimeout(timer);
        };
    }, [audioUrl]);

    return (
        <div className="message-audio" data-message-id={messageId}>
            <button
                type="button"
                onClick={handlePlayPause}
                className={`play-btn ${isPlaying ? 'playing' : ''} ${isLoading ? 'loading' : ''}`}
                aria-label={isPlaying ? 'Pause' : 'Play'}
                disabled={isLoading}
            >
                {isLoading ? (
                    <span className="spinner" />
                ) : isPlaying ? (
                    '⏸️'
                ) : (
                    '▶️'
                )}
            </button>

            <div className="audio-controls">
                <div 
                    className="progress-container"
                    onClick={handleProgressClick}
                >
                    <div 
                        className={`progress-bar ${isPlaying ? 'active' : ''}`}
                        style={{ width: `${Math.min(progress, 100)}%` }}
                    />
                </div>
                <span className="duration">
                    {isLoading ? '--:--' : formatTime(duration)}
                </span>
            </div>

            {timestamp && <span className="timestamp">{timestamp}</span>}
        </div>
    );
}

export default MessageAudio;
