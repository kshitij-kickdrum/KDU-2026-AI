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

    /**
     * Accepts a validated request and returns the correct HTTP status for creation.
     */
    @PostMapping
    public ResponseEntity<UserResponseDto> createUser(
        @Valid @RequestBody UserRequestDto request
    ) {
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
