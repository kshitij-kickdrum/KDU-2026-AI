## Updated controller code

```java
package com.example.usermanagement.controller;

import com.example.usermanagement.dto.UserRequestDto;
import com.example.usermanagement.dto.UserResponseDto;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private static final Logger logger = LoggerFactory.getLogger(UserController.class);

    /**
     * Accepts a user creation request and returns a simple success response.
     */
    @PostMapping
    public ResponseEntity<UserResponseDto> createUser(@Valid @RequestBody UserRequestDto request) {
        logger.info(
            "event=user_create_request endpoint=/api/users hasName={} hasEmail={}",
            hasText(request.getName()),
            hasText(request.getEmail())
        );

        String successMessage = "User created successfully for " + request.getName();
        logger.info("event=user_create_success endpoint=/api/users");
        return ResponseEntity.ok(UserResponseDto.success(successMessage));
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
```

## Updated exception handler

```java
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
```

## Short explanation

The endpoint now uses structured SLF4J logs with stable `key=value` style messages. The controller logs incoming requests and successful user creation without printing the raw name or email, while the global handler logs validation failures and unexpected exceptions with enough context for troubleshooting.
