# STRING pointer and overflow experiment

## Hypothesis
STRING may diverge when POINTER is supplied, multiple senders are concatenated, or the receiver has insufficient capacity.

## Required behavior
- POINTER is one-based and advances by the number of characters transferred.
- Delimiters are applied per sender.
- Characters outside the receiver's active range remain unchanged.
- ON OVERFLOW and NOT ON OVERFLOW select the correct branch.
- Receiver truncation and pointer state match GnuCOBOL.

## Acceptance matrix
- One and multiple senders.
- DELIMITED BY SIZE and DELIMITED BY literal/identifier.
- Initial pointer values 1, middle, and receiver length + 1.
- Overflow exactly at capacity and beyond capacity.
- Nested STRING statements sharing a receiver.

## Measurement
Implement differential tests first; benchmark only after unit tests pass. The 500-case external holdout is the score source of truth.