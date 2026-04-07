package com.example.usermanagement.service;

import com.example.usermanagement.dto.UserCreatedResponseDto;
import com.example.usermanagement.dto.UserRequestDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    private static final Logger logger = LoggerFactory.getLogger(UserService.class);

    /**
     * Encapsulates the user creation workflow.
     * Persistence is omitted here, but this is the correct place for it.
     */
    public UserCreatedResponseDto createUser(UserRequestDto request) {
        logger.info(
            "event=user_create_success service=UserService hasName={} hasEmail={}",
            hasText(request.name()),
            hasText(request.email())
        );

        return new UserCreatedResponseDto("CREATED");
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
