from django.core.management.base import BaseCommand
from core.models import Question

class Command(BaseCommand):
    help = 'Populates the database with coding questions.'

    def handle(self, *args, **kwargs):
        questions_data = {
            1: {
                "text": "Write a Python function `test_distinct(data)` that takes a sequence of numbers and determines whether all the numbers are different from each other.",
                "test_case": "print(test_distinct([1, 5, 7, 9]))\nprint(test_distinct([2, 4, 5, 5, 7, 9]))",
                "expected_output": "True\nFalse\n",
                "test_case_display": "print(test_distinct([1, 5, 7, 9]))\nprint(test_distinct([2, 4, 5, 5, 7, 9]))"
            },
            2: {
                "text": "Write a Python program to identify unique triplets whose three elements sum to zero from an array of n integers. The function should be named `three_sum`.",
                "test_case": "print(three_sum([1, -6, 4, 2, -1, 2, 0, -2, 0]))",
                "expected_output": "[(-2, 0, 2), (-1, 0, 1)]\n",
                "test_case_display": "print(three_sum([1, -6, 4, 2, -1, 2, 0, -2, 0]))"
            },
            3: {
                "text": "Write a Python program to find the digits that are missing from a given mobile number. The function should be named `absent_digits`.",
                "test_case": "print(absent_digits([9, 8, 3, 2, 2, 0, 9, 7, 6, 3]))",
                "expected_output": "[1, 4, 5]\n",
                "test_case_display": "print(absent_digits([9, 8, 3, 2, 2, 0, 9, 7, 6, 3]))"
            },
            4: {
                "text": "Write a Python program to find the number of zeros at the end of a factorial of a given positive number. The function should be named `factendzero`.",
                "test_case": "print(factendzero(100))",
                "expected_output": "24\n",
                "test_case_display": "print(factendzero(100))"
            },
            5: {
                "text": "Write a Python program to get the third side of a right-angled triangle from two given sides. The function should be named `pythagoras`.",
                "test_case": "print(pythagoras(3, 4, 'x'))\nprint(pythagoras(3, 'x', 5))",
                "expected_output": "Opposite = 5.0\nAdjacent = 4.0\n",
                "test_case_display": "print(pythagoras(3, 4, 'x'))\nprint(pythagoras(3, 'x', 5))"
            },
            6: {
                "text": "Write a Python program to find the median among three given numbers. The function should be named `find_median`.",
                "test_case": "print(find_median(3, 8, 5))",
                "expected_output": "5\n",
                "test_case_display": "print(find_median(3, 8, 5))"
            },
            7: {
                "text": "Write a Python program to find the total number of even or odd divisors of a given integer. The function should be named `divisor`.",
                "test_case": "print(divisor(15))",
                "expected_output": "4\n",
                "test_case_display": "print(divisor(15))"
            },
            8: {
                "text": "Write a Python program to compute the summation of the absolute difference of all distinct pairs in a given array (non-decreasing order). The function should be named `sum_distinct_pairs`.",
                "test_case": "print(sum_distinct_pairs([1, 2, 3]))",
                "expected_output": "4\n",
                "test_case_display": "print(sum_distinct_pairs([1, 2, 3]))"
            },
            9: {
                "text": "Write a Python program to find common divisors between two numbers in a given pair. The function should be named `num_comm_div`.",
                "test_case": "print(num_comm_div(12, 24))",
                "expected_output": "6\n",
                "test_case_display": "print(num_comm_div(12, 24))"
            },
            10: {
                "text": "Write a Python program to reverse the digits of a given number and add them to the original. Repeat this procedure if the sum is not a palindrome. The function should be named `rev_number`.",
                "test_case": "print(rev_number(1234))",
                "expected_output": "5555\n",
                "test_case_display": "print(rev_number(1234))"
            },
            11: {
                "text": "Write a Python program to check whether three given lengths (integers) of three sides form a right triangle. Print 'Yes' or 'No'. The function should be named `is_right_triangle`.",
                "test_case": "print(is_right_triangle(8, 6, 7))\nprint(is_right_triangle(3, 4, 5))",
                "expected_output": "No\nYes\n",
                "test_case_display": "print(is_right_triangle(8, 6, 7))\nprint(is_right_triangle(3, 4, 5))"
            },
            12: {
                "text": "Write a Python program to compute the amount of debt in n months. The function should be named `compute_debt`.",
                "test_case": "print(compute_debt(7))",
                "expected_output": "144000\n",
                "test_case_display": "print(compute_debt(7))"
            },
            13: {
                "text": "Write a Python program that reads an integer n and finds the number of combinations of a,b,c and d (0 = a,b,c,d = 9) where (a + b + c + d) will be equal to n. The function should be named `count_combinations`.",
                "test_case": "import itertools\nprint(count_combinations(15))",
                "expected_output": "592\n",
                "test_case_display": "import itertools\nprint(count_combinations(15))"
            },
            14: {
                "text": "Write a Python program to find the number of prime numbers that are less than or equal to a given number. The function should be named `count_primes`.",
                "test_case": "print(count_primes(35))",
                "expected_output": "11\n",
                "test_case_display": "print(count_primes(35))"
            },
            15: {
                "text": "Write a Python program to compute and print the sum of two given integers. If the sum exceeds 80 digits, print 'Overflow!'. The function should be named `safe_sum`.",
                "test_case": "print(safe_sum(50, 30))\nprint(safe_sum(10**79, 10**79))",
                "expected_output": "80\nOverflow!\n",
                "test_case_display": "print(safe_sum(50, 30))\nprint(safe_sum(10**79, 10**79))"
            },
            16: {
                "text": "Write a Python program that accepts six numbers as input and sorts them in descending order. The function should be named `sort_descending`.",
                "test_case": "print(sort_descending([15, 30, 25, 14, 35, 40]))",
                "expected_output": "40 35 30 25 15 14\n",
                "test_case_display": "print(sort_descending([15, 30, 25, 14, 35, 40]))"
            },
            17: {
                "text": "Write a Python program to reverse only the vowels of a given string. The function should be named `reverse_vowels`.",
                "test_case": "print(reverse_vowels('w3resource'))",
                "expected_output": "w3r**o**s**u**rc**e**\n",
                "test_case_display": "print(reverse_vowels('w3resource'))"
            },
            18: {
                "text": "Write a Python program to check whether a given integer is a palindrome or not. The function should be named `is_palindrome`.",
                "test_case": "print(is_palindrome(252))\nprint(is_palindrome(100))",
                "expected_output": "True\nFalse\n",
                "test_case_display": "print(is_palindrome(252))\nprint(is_palindrome(100))"
            },
            19: {
                "text": "Write a Python program that removes duplicate elements from a given array of numbers so that each element appears only once and returns the new length of the array. The function should be named `remove_duplicates`.",
                "test_case": "print(remove_duplicates([1, 2, 2, 3, 4, 4]))",
                "expected_output": "4\n",
                "test_case_display": "print(remove_duplicates([1, 2, 2, 3, 4, 4]))"
            },
            20: {
                "text": "Write a Python program to find the longest common prefix string among a given array of strings. The function should be named `longest_Common_Prefix`.",
                "test_case": "print(longest_Common_Prefix(['abcdefgh', 'abcefgh']))\nprint(longest_Common_Prefix(['Python', 'PHP', 'Perl']))",
                "expected_output": "abc\n\n",
                "test_case_display": "print(longest_Common_Prefix(['abcdefgh', 'abcefgh']))\nprint(longest_Common_Prefix(['Python', 'PHP', 'Perl']))"
            },
            21: {
                "text": "Write a Python function `is_even_or_odd(number)` that returns \"Even\" if the number is even and \"Odd\" if the number is odd.",
                "test_case": "print(is_even_or_odd(4))\nprint(is_even_or_odd(7))",
                "expected_output": "Even\nOdd\n",
                "test_case_display": "print(is_even_or_odd(4))\nprint(is_even_or_odd(7))"
            },
            22: {
                "text": "Write a Python function `reverse_string(s)` that reverses a given string `s`.",
                "test_case": "print(reverse_string('hello'))",
                "expected_output": "olleh\n",
                "test_case_display": "print(reverse_string('hello'))"
            },
            23: {
                "text": "Write a Python function `find_max(numbers)` that takes a list of numbers and returns the largest number in the list.",
                "test_case": "print(find_max([10, 5, 25, 15]))",
                "expected_output": "25\n",
                "test_case_display": "print(find_max([10, 5, 25, 15]))"
            },
        }

        Question.objects.all().delete()

        # Add questions to the database
        for q_id, q_data in questions_data.items():
            Question.objects.create(
                id=q_id,
                question_text=q_data['text'],
                test_case=q_data['test_case'],
                expected_output=q_data['expected_output'],
                test_case_display=q_data['test_case_display']
            )

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with questions!'))