package com.example.usermanagement.exception;

import com.example.usermanagement.dto.UserResponseDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.LinkedHashMap;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger logger = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /**
     * Converts bean validation failures into a stable error response format.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<UserResponseDto> handleValidationException(MethodArgumentNotValidException exception) {
        Map<String, String> errors = new LinkedHashMap<>();

        for (FieldError fieldError : exception.getBindingResult().getFieldErrors()) {
            errors.put(fieldError.getField(), fieldError.getDefaultMessage());
        }

        logger.warn(
            "event=user_create_validation_failed endpoint=/api/users errorCount={} fields={}",
            errors.size(),
            errors.keySet()
        );

        UserResponseDto response = UserResponseDto.failure(
            "Validation failed",
            errors
        );

        return ResponseEntity.badRequest().body(response);
    }

    /**
     * Catches unexpected failures and prevents raw exception details from leaking to clients.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<UserResponseDto> handleGenericException(Exception exception) {
        logger.error(
            "event=user_create_exception endpoint=/api/users exceptionType={}",
            exception.getClass().getSimpleName(),
            exception
        );

        UserResponseDto response = UserResponseDto.failure(
            "An internal server error occurred",
            Map.of("server", "Please contact support or try again later")
        );

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }
}
