package com.example.usermanagement.dto;

import java.util.Map;

/**
 * Shared API response used for both successful and failed requests.
 */
public class UserResponseDto {

    private final boolean success;
    private final String message;
    private final Map<String, String> errors;

    public UserResponseDto(boolean success, String message, Map<String, String> errors) {
        this.success = success;
        this.message = message;
        this.errors = errors;
    }

    public static UserResponseDto success(String message) {
        return new UserResponseDto(true, message, Map.of());
    }

    public static UserResponseDto failure(String message, Map<String, String> errors) {
        return new UserResponseDto(false, message, errors);
    }

    public boolean isSuccess() {
        return success;
    }

    public String getMessage() {
        return message;
    }

    public Map<String, String> getErrors() {
        return errors;
    }
}
