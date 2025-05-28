# This is a test file to see the indentation
                    account_info = self._read_twitter_account_info(primary_username)
                else:
                    # For Instagram, use existing method
                    account_info = self._read_account_info(primary_username)

            # Process data based on platform
            if platform == 'twitter':
                # Process Twitter data with new format
                data = self.process_twitter_data(raw_data, account_info)
            else:
                # Process Instagram data (existing logic)
                if isinstance(raw_data, list) and raw_data and 'latestPosts' in raw_data[0]:
                    data = self.process_instagram_data(raw_data, account_info)
