library(tidyverse)
# Read in inferred Xpaths (based on XSD).
inferred <- read_csv("./data/xpath_all.csv")

inferred <- inferred %>%
  group_by(-Version) %>%
  arrange(Version) %>%
  summarise(Versions = paste(Version, collapse = "; ")) %>%
  ungroup()

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
write_csv(confirmed, "./output/confirmed.csv")

predicted <- anti_join(inferred, actual, by = "Xpath")
write_csv(predicted, "./output/predicted.csv")

observed <- anti_join(actual, inferred, by = "Xpath")
write_csv(observed, "./output/observed.csv")
