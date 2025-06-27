#!/usr/bin/env python
"""Fix cosine similarity function"""

import sys

sys.path.insert(0, ".")

from src.config import get_session


def main():
    session = get_session()

    try:
        print("Fixing cosine similarity function...")

        session.sql("USE DATABASE MUED").collect()

        # Drop existing function if exists
        try:
            session.sql(
                "DROP FUNCTION IF EXISTS STG.COSINE_SIMILARITY(ARRAY, ARRAY)"
            ).collect()
        except:
            pass

        # Create a simpler version of cosine similarity
        session.sql(
            """
            CREATE OR REPLACE FUNCTION STG.COSINE_SIMILARITY(v1 ARRAY, v2 ARRAY)
            RETURNS FLOAT
            LANGUAGE JAVASCRIPT
            AS $$
                if (!V1 || !V2 || V1.length !== V2.length || V1.length === 0) {
                    return null;
                }

                let dotProduct = 0;
                let norm1 = 0;
                let norm2 = 0;

                for (let i = 0; i < V1.length; i++) {
                    dotProduct += V1[i] * V2[i];
                    norm1 += V1[i] * V1[i];
                    norm2 += V2[i] * V2[i];
                }

                if (norm1 === 0 || norm2 === 0) {
                    return 0;
                }

                return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
            $$
        """
        ).collect()

        print("✓ Cosine similarity function fixed!")

        # Test the function
        test_result = session.sql(
            """
            SELECT STG.COSINE_SIMILARITY([1,2,3], [1,2,3]) as test
        """
        ).collect()
        print(f"Test result: {test_result[0]['TEST']} (should be 1.0)")

        session.close()

    except Exception as e:
        print(f"Error: {e}")
        session.close()


if __name__ == "__main__":
    main()
