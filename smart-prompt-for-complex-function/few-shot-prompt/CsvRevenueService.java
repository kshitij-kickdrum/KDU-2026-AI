package com.example.csvprocessing.service;

import com.example.csvprocessing.dto.CategoryRevenueDto;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class CsvRevenueService {

    /**
     * Reads a CSV file, keeps only active rows, groups by category, calculates
     * average revenue, and returns the result sorted by average revenue descending.
     */
    public List<CategoryRevenueDto> getAverageRevenueByCategory(Path csvFilePath) throws IOException {
        Map<String, RevenueStats> revenueByCategory = new HashMap<>();

        try (BufferedReader reader = Files.newBufferedReader(csvFilePath)) {
            String line = reader.readLine(); // Skip header row.
            if (line == null) {
                return List.of();
            }

            while ((line = reader.readLine()) != null) {
                String[] columns = line.split(",", -1);
                if (columns.length < 3) {
                    continue;
                }

                String category = columns[0].trim();
                String status = columns[1].trim();
                Double revenue = parseRevenue(columns[2]);

                // Ignore incomplete, inactive, or invalid rows.
                if (category.isEmpty() || !"active".equalsIgnoreCase(status) || revenue == null) {
                    continue;
                }

                revenueByCategory
                    .computeIfAbsent(category, ignored -> new RevenueStats())
                    .addRevenue(revenue);
            }
        }

        List<CategoryRevenueDto> results = new ArrayList<>();
        for (Map.Entry<String, RevenueStats> entry : revenueByCategory.entrySet()) {
            results.add(new CategoryRevenueDto(entry.getKey(), entry.getValue().getAverageRevenue()));
        }

        results.sort(Comparator
            .comparingDouble(CategoryRevenueDto::getAverageRevenue)
            .reversed()
            .thenComparing(CategoryRevenueDto::getCategory));

        return results;
    }

    /**
     * Converts the revenue column to a number and safely skips bad values.
     */
    private Double parseRevenue(String revenueValue) {
        if (revenueValue == null || revenueValue.trim().isEmpty()) {
            return null;
        }

        try {
            return Double.parseDouble(revenueValue.trim());
        } catch (NumberFormatException exception) {
            return null;
        }
    }

    private static final class RevenueStats {

        private double totalRevenue;
        private int count;

        private void addRevenue(double revenue) {
            totalRevenue += revenue;
            count++;
        }

        private double getAverageRevenue() {
            return count == 0 ? 0.0 : totalRevenue / count;
        }
    }
}
