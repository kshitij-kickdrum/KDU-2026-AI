## Bug

The endpoint returns `200 OK` for a successful create request. A `POST` that creates a user should return `201 Created`.

## Cause

The controller uses `ResponseEntity.ok(...)`, which hardcodes HTTP 200.

## Corrected code

```java
package com.example.usermanagement.controller;

import com.example.usermanagement.dto.UserRequestDto;
import com.example.usermanagement.dto.UserResponseDto;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private static final Logger logger = LoggerFactory.getLogger(UserController.class);

    @PostMapping
    public ResponseEntity<UserResponseDto> createUser(@Valid @RequestBody UserRequestDto request) {
        logger.info(
            "event=user_create_request endpoint=/api/users hasName={} hasEmail={}",
            hasText(request.name()),
            hasText(request.email())
        );

        String successMessage = "User created successfully for " + request.name();
        logger.info("event=user_create_success endpoint=/api/users");

        return ResponseEntity
            .status(HttpStatus.CREATED)
            .body(UserResponseDto.success(successMessage));
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
```

## What changed

Only the controller response status changed. The request DTO, response DTO, validation rules, exception handling, and logging approach stay the same.

## Previous broader refactor

The files below remain from the earlier context-window-management example, but they are not part of this focused snippet-level fix:

```text
ApiResponse.java
GlobalExceptionHandler.java
UserCreatedResponseDto.java
UserRequestDto.java
UserService.java
```
