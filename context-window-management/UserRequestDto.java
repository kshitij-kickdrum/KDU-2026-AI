package com.example.usermanagement.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

/**
 * Request body for creating a user through the REST API.
 */
public record UserRequestDto(
    @NotBlank(message = "Name must not be blank")
    String name,

    @NotBlank(message = "Email must not be blank")
    @Email(message = "Email must be a valid email address")
    String email
) {
}
