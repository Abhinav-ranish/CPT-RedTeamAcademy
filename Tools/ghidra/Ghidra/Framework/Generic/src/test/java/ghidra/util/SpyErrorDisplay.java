/* ###
 * IP: GHIDRA
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *      http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package ghidra.util;

import static org.junit.Assert.fail;

import java.awt.Component;
import java.util.Arrays;
import java.util.Iterator;

import ghidra.util.datastruct.LRUSet;

/**
 * An {@link ErrorDisplay} implementation that lets you track log messages during testing
 */
public class SpyErrorDisplay implements ErrorDisplay, Iterable<String> {

	private LRUSet<String> messages = new LRUSet<>(100);

	@Override
	public void displayInfoMessage(ErrorLogger errorLogger, Object originator, Component parent,
			String title, Object message) {
		messages.add("INFO: " + String.valueOf(message));
	}

	@Override
	public void displayErrorMessage(ErrorLogger errorLogger, Object originator, Component parent,
			String title, Object message, Throwable throwable) {
		messages.add("ERROR: " + String.valueOf(message));
	}

	@Override
	public void displayWarningMessage(ErrorLogger errorLogger, Object originator, Component parent,
			String title, Object message, Throwable throwable) {
		messages.add("WARNING: " + String.valueOf(message));
	}

	@Override
	public Iterator<String> iterator() {
		return messages.iterator();
	}

	public void reset() {
		messages.clear();
	}

	public void assertDisplayMessage(String... words) {
		for (String message : this) {
			if (StringUtilities.containsAllIgnoreCase(message, words)) {
				return;
			}
		}

		fail("Did not find log message containing all these words: " + Arrays.toString(words) +
			"\nInstead, had these messages: " + toString());
	}

	@Override
	public String toString() {
		return messages.toString();
	}
}
