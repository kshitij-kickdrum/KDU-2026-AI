package com.example.usermanagement.dto;

import java.time.Instant;
import java.util.List;
import java.util.Map;

/**
 * Standard API envelope shared by successful and failed responses.
 */
public record ApiResponse<T>(
    boolean success,
    String message,
    T data,
    Map<String, List<String>> errors,
    Instant timestamp
) {

    public static <T> ApiResponse<T> success(String message, T data) {
        return new ApiResponse<>(true, message, data, Map.of(), Instant.now());
    }

    public static <T> ApiResponse<T> failure(String message, Map<String, List<String>> errors) {
        return new ApiResponse<>(false, message, null, errors, Instant.now());
    }
}
