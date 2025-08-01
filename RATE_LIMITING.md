# Gemini API Rate Limiting Implementation

This document explains how the rate limiting system for Gemini API has been implemented to handle quota exceeded errors (`429 Too Many Requests`).

## Problem

The system was encountering quota limit errors from the Gemini API:
```
429 You exceeded your current quota, please check your plan and billing details.
quota_id: "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"
```

## Solution

An adaptive rate limiting system has been implemented that:

1. Enforces minimum delays between API calls
2. Increases delays after encountering quota errors
3. Respects API-suggested retry times
4. Gradually reduces delays after consecutive successful calls
5. Adds randomization to prevent synchronized requests

## Implementation Summary

The following changes were made:

1. Created a new `AdaptiveRateLimiter` class in `rag_implementation.py`
2. Added rate limiting integration to `RagImplementation.generate_recommendation` method
3. Added quota error detection and handling in both main modules:
   - `rag_implementation.py`
   - `recommendation_generation.py`
4. Added intelligent retry logic with extraction of API-suggested retry times
5. Added progressive backoff and cooldown mechanisms
6. Added test functions to verify the rate limiter's behavior

## Test Results

The rate limiter has been successfully tested, showing proper behavior for:
- Basic rate limiting enforcement
- Success tracking and delay reduction
- Error handling and backoff
- Quota error specific handling with retry timing
- Appropriate waiting periods

```
=== Testing Adaptive Rate Limiter ===
Initial delay: 5s

1. Testing basic wait...
Wait time: 0.00s

2. Recording 3 successful calls...
After success 1: delay = 5.00s
After success 2: delay = 5.00s
After success 3: delay = 4.50s

3. Recording error (not quota)...
After error: delay = 6.75s

4. Recording quota error with retry seconds...
After quota error: delay = 10.00s, retry_after = 10s

5. Testing wait after quota error...
Wait after quota error: 11.19s
```

## How It Works

The rate limiting system consists of the `AdaptiveRateLimiter` class in `rag_implementation.py` with the following features:

### Key Methods

- `wait_if_needed()`: Enforces appropriate waiting periods before API calls
- `record_success()`: Records successful calls and potentially reduces delay
- `record_error(is_quota_error, retry_seconds)`: Handles error conditions and increases delays

### Default Configuration

The rate limiter is initialized with these default settings:

```python
AdaptiveRateLimiter(
    initial_delay=60,     # Start with 60s between calls
    min_delay=30,         # Never go below 30s
    max_delay=120,        # Never exceed 120s
    backoff_factor=1.5,   # Multiply delay by this after errors
    success_factor=0.9    # Multiply delay by this after successes
)
```

### Handling Quota Errors

When a quota error occurs:

1. The system extracts the suggested retry delay from the error message
2. It adds a small buffer to the suggested retry time
3. It records the error and adjusts the delay for future calls
4. It implements the waiting period before the next attempt

## How to Adjust Settings

You can modify the rate limiter behavior by adjusting the parameters in `rag_implementation.py`:

1. **For more aggressive rate limiting** (if still hitting quota errors):
   ```python
   self.rate_limiter = AdaptiveRateLimiter(
       initial_delay=90,    # Start with 90s delay 
       min_delay=60,        # Never go below 60s
       max_delay=180        # Allow up to 3 minutes delay
   )
   ```

2. **For faster operation** (if your quota permits):
   ```python
   self.rate_limiter = AdaptiveRateLimiter(
       initial_delay=45,    # Start with 45s delay
       min_delay=15,        # Allow as low as 15s between calls
       max_delay=90         # Cap at 90s max delay
   )
   ```

## Testing the Rate Limiter

You can test the rate limiter independently with:

```bash
python rag_implementation.py test_rate_limiter
```

## Implementation Location

The rate limiter has been integrated in:

1. `rag_implementation.py` - Primary implementation and API call handling
2. `recommendation_generation.py` - Secondary integration for downstream components

## Best Practices

1. **Production Environment**: Use the more conservative settings to ensure reliable operation
2. **Development Environment**: You can use faster settings for testing
3. **Cost Management**: The rate limiter helps stay within free tier limits by spreading requests over time

## Monitoring

The system logs detailed information about rate limiting:
- Current delays
- Wait times
- Quota error handling
- Retry attempts

Monitor these logs to fine-tune the rate limiting for your specific usage patterns.

## Expected Impact

With this implementation:

1. **Quality Maintained**: The system will continue to generate high-quality content using the Gemini API
2. **Reliability Improved**: Rate limit errors should be dramatically reduced
3. **Performance Trade-off**: Operations will take longer but be more reliable
4. **Adaptive Behavior**: The system will automatically adjust to changing API conditions

## Future Improvements

Potential future enhancements:
1. Implement a shared rate limiter singleton for multi-process applications
2. Add persistent rate limit state to survive application restarts
3. Implement token bucket algorithm for more precise rate control
4. Add global quota monitoring and priority queue for critical requests 