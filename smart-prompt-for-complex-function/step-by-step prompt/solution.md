## DTO class

```java
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
```

## Service method

```java
package com.example.csvprocessing.service;

import com.example.csvprocessing.dto.CategoryRevenueAverageDto;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
public class CsvRevenueService {

    /**
     * Reads CSV data, keeps active rows, groups them by category, calculates average revenue,
     * and returns the result sorted by average revenue in descending order.
     */
    public List<CategoryRevenueAverageDto> calculateAverageRevenueByCategory(Path csvFilePath) throws IOException {
        Map<String, RevenueAccumulator> revenueByCategory = new LinkedHashMap<>();

        try (BufferedReader reader = Files.newBufferedReader(csvFilePath)) {
            String line = reader.readLine();
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
                BigDecimal revenue = parseRevenueSafely(columns[2]);

                // Skip incomplete rows, inactive rows, and rows with invalid revenue.
                if (category.isEmpty() || !"active".equalsIgnoreCase(status) || revenue == null) {
                    continue;
                }

                revenueByCategory
                    .computeIfAbsent(category, ignored -> new RevenueAccumulator())
                    .addRevenue(revenue);
            }
        }

        return revenueByCategory.entrySet()
            .stream()
            .map(entry -> new CategoryRevenueAverageDto(
                entry.getKey(),
                entry.getValue().calculateAverage()
            ))
            .sorted(Comparator.comparing(CategoryRevenueAverageDto::getAverageRevenue).reversed()
                .thenComparing(CategoryRevenueAverageDto::getCategory))
            .collect(Collectors.toCollection(ArrayList::new));
    }

    /**
     * Converts the revenue column to BigDecimal. Invalid or missing values are ignored safely.
     */
    private BigDecimal parseRevenueSafely(String revenueValue) {
        if (revenueValue == null || revenueValue.trim().isEmpty()) {
            return null;
        }

        try {
            return new BigDecimal(revenueValue.trim());
        } catch (NumberFormatException exception) {
            return null;
        }
    }

    private static final class RevenueAccumulator {

        private BigDecimal totalRevenue = BigDecimal.ZERO;
        private int rowCount = 0;

        private void addRevenue(BigDecimal revenue) {
            totalRevenue = totalRevenue.add(Objects.requireNonNull(revenue));
            rowCount++;
        }

        private BigDecimal calculateAverage() {
            if (rowCount == 0) {
                return BigDecimal.ZERO;
            }

            return totalRevenue.divide(BigDecimal.valueOf(rowCount), 2, RoundingMode.HALF_UP);
        }
    }
}
```

## Short explanation

The service reads the CSV file line by line, skips the header, parses `category`, `status`, and `revenue`, and keeps only rows where `status` is `active`. It ignores rows with missing or invalid revenue values, accumulates totals and counts per category, converts those aggregates into DTO objects with averaged revenue, and then sorts the final list by average revenue in descending order.
