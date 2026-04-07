package com.example.usermanagement.exception;

import com.example.usermanagement.dto.ApiResponse;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger logger = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /**
     * Returns all validation messages per field instead of overwriting repeated failures.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidationException(
        MethodArgumentNotValidException exception,
        HttpServletRequest request
    ) {
        Map<String, List<String>> errors = new LinkedHashMap<>();

        for (FieldError fieldError : exception.getBindingResult().getFieldErrors()) {
            errors.computeIfAbsent(fieldError.getField(), ignored -> new java.util.ArrayList<>())
                .add(fieldError.getDefaultMessage());
        }

        logger.warn(
            "event=user_create_validation_failed endpoint={} errorCount={} fields={}",
            request.getRequestURI(),
            exception.getErrorCount(),
            errors.keySet()
        );

        return ResponseEntity
            .badRequest()
            .body(ApiResponse.failure("Validation failed", errors));
    }

    /**
     * Handles malformed JSON bodies with the same response shape as other errors.
     */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiResponse<Void>> handleUnreadableMessage(
        HttpMessageNotReadableException exception,
        HttpServletRequest request
    ) {
        logger.warn(
            "event=user_create_bad_request endpoint={} reason=malformed_json",
            request.getRequestURI()
        );

        return ResponseEntity
            .badRequest()
            .body(ApiResponse.failure(
                "Malformed request body",
                Map.of("request", List.of("Request body could not be parsed"))
            ));
    }

    /**
     * Prevents unhandled exceptions from leaking internal details to clients.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGenericException(
        Exception exception,
        HttpServletRequest request
    ) {
        logger.error(
            "event=user_create_exception endpoint={} exceptionType={}",
            request.getRequestURI(),
            exception.getClass().getSimpleName(),
            exception
        );

        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ApiResponse.failure(
                "An internal server error occurred",
                Map.of("server", List.of("Please contact support or try again later"))
            ));
    }
}
