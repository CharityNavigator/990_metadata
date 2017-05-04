library(tidyverse)
# Read in inferred Xpaths (based on XSD).
inferred <- read_csv("./data/xpath_all.csv")

# Read and prepare counts of actual Xpaths by version.
actual <- read_csv("./data/counts.csv", col_names = FALSE) %>%
  setNames(c("Version", "Xpath", "Count"))

# Delete internal nodes from counts
internal <- read_csv("./data/internal_nodes.csv", col_names = FALSE)$X1

actual <- actual %>%
  filter(!Xpath %in% internal) %>%
  mutate(Xpath = sprintf("/Return/%s", Xpath)) %>%
  spread(Version, Count)

# Inner join xpaths and counts.
confirmed <- inner_join(inferred, actual, by = "Xpath")

predicted <- anti_join(inferred, actual, by = "Xpath")

observed <- anti_join(actual, inferred, by = "Xpath")
# Identify observed-but-not-predicted.

# Identify predicted-but-not-observed.