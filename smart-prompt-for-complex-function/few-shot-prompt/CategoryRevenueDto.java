package com.example.csvprocessing.dto;

/**
 * DTO returned by the service after calculating average revenue per category.
 */
public class CategoryRevenueDto {

    private final String category;
    private final double averageRevenue;

    public CategoryRevenueDto(String category, double averageRevenue) {
        this.category = category;
        this.averageRevenue = averageRevenue;
    }

    public String getCategory() {
        return category;
    }

    public double getAverageRevenue() {
        return averageRevenue;
    }
}
