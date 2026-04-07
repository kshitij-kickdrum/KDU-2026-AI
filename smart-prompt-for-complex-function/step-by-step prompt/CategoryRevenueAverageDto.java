package com.example.csvprocessing.dto;

import java.math.BigDecimal;

/**
 * DTO returned to callers after aggregating CSV rows by category.
 */
public class CategoryRevenueAverageDto {

    private final String category;
    private final BigDecimal averageRevenue;

    public CategoryRevenueAverageDto(String category, BigDecimal averageRevenue) {
        this.category = category;
        this.averageRevenue = averageRevenue;
    }

    public String getCategory() {
        return category;
    }

    public BigDecimal getAverageRevenue() {
        return averageRevenue;
    }
}
