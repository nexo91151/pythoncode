from collections import Counter

note = "patient has diabetes patient needs followup"
words=note.lower().split()
print(words)
word_count=Counter(words)
print(word_count, end =" ")
