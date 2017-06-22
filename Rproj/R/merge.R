library(tidyverse)
# Read in inferred Xpaths (based on XSD).
inferred <- read_csv("./data/xpath_all.csv") %>%
  distinct() %>%
  mutate(Xpath = sprintf("/%s", Xpath)) %>%
  group_by(Xpath, Source, Type, Description, Line, MinOccur, MaxOccur) %>%
  arrange(Version) %>%
  summarise(Versions = paste(Version, collapse = "; ")) %>%
  ungroup() %>%
  select(c(Versions, everything()))

# Read and prepare counts of actual Xpaths by version.
actual <- read_csv("./data/counts.csv", col_names = FALSE) %>%
  setNames(c("Version", "Xpath", "Count"))

# Delete internal nodes from counts
internal <- read_csv("./data/internal_nodes.csv", col_names = FALSE)$X1

actual <- actual %>%
  filter(!Xpath %in% internal) %>%
  mutate(Xpath = sprintf("/Return/%s", Xpath)) %>%
  spread(Version, Count)

confirmed <- inner_join(inferred, actual, by = "Xpath")
write_csv(confirmed, "./output/confirmed.csv", na = "")

predicted <- anti_join(inferred, actual, by = "Xpath")
write_csv(predicted, "./output/predicted.csv", na = "")

observed <- anti_join(actual, inferred, by = "Xpath")
write_csv(observed, "./output/observed.csv", na = "")

master_file <- right_join(inferred, actual, by = "Xpath")
write_csv(master_file, "./output/master_file.csv", na = "")

# Things that we think we should be able to identify, but can't
most_concern <- observed %>%
  gather(Version, Count, -Xpath) %>%
  filter(!is.na(Count)) %>%
  filter(!(stringr::str_detect(Version, "2011"))) %>%   # Missing; infer from observed
  filter(!(stringr::str_detect(Version, "2012"))) %>%   # Missing; infer from observed
  group_by(Xpath) %>%
  arrange(desc(Count)) %>%
  mutate(CountAll = sum(Count)) %>%
  top_n(1, Count) %>%
  ungroup() %>%
  arrange(desc(CountAll))

write_csv(most_concern, "./output/most_concern.csv", na = "")

# Merge in contributions from datathon
load_and_clean <- function(fn) {
  readxl::read_excel(fn, col_names = FALSE, skip = 1) %>%
    mutate(fn = fn) %>%
    select(X3)
}
contrib_files <- list.files("./data/contribs", full.names = TRUE)
contribs <- lapply(contrib_files, load_and_clean )

contribs_df <- bind_rows(contribs) %>%
  filter(!is.na(X3))

contrib_files[[1]]
readxl::read_excel(contrib_files[[1]], col_names = FALSE, skip = 1)
# Any xpaths used more than once?
repeated_xp <- contribs_df %>%
  filter(!is.na(X3)) %>%
  group_by(X3) %>%
  summarise(n = n()) %>%
  ungroup() %>%
  filter(n > 1)

sources <- master_file %>%
  group_by(Source) %>%
  summarise()

# Get any xpaths not yet processed

total <- master_file %>%
  filter(stringr::str_detect(Xpath, "IRS990(EZ)?/"))

not_processed_head <- anti_join(master_file, contribs_df, by = c("Xpath" = "X3")) %>%
  filter(Source == "ReturnHeader990x") 

write_csv(not_processed_head, "./output/not_processed_head.csv", na = "")
  filter(stringr::str_detect(Xpath, "IRS990(EZ)?/"))

write_csv(not_processed_xp, "./output/not_processed_xp.csv", na = "")

head(contribs_df)

load_and_clean <- function(fn) {
  readxl::read_excel(fn, col_names = FALSE, skip = 1) %>%
    mutate(fn = fn) %>%
    select(X0)
}
contrib_files <- list.files("./data/contribs", full.names = TRUE)
contribs <- lapply(contrib_files, load_and_clean )

contribs_df <- bind_rows(contribs) %>%
  filter(!is.na(X0))

contribs_df %>%
  group_by(X0) %>%
  summarise() %>%
  ungroup() %>%
  summarise(n = n())