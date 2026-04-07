DTO class:
`CategoryRevenueAverageDto` stores the category name and its average revenue so the service can return a clean `List` of response objects.

Service method:
`CsvRevenueService#calculateAverageRevenueByCategory` reads the CSV file line by line, skips the header, parses `category`, `status`, and `revenue`, filters to `active` rows only, ignores invalid or missing revenue values, groups rows by category, computes the average with `BigDecimal`, and sorts the DTO list by average revenue in descending order.

How it works:
The method uses a small accumulator object to track total revenue and row count for each category. After reading the whole file, it converts each category aggregate into a DTO, sorts the final list, and returns it in a Spring Boot friendly form.
