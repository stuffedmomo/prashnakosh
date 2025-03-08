from django import forms
from django.core.validators import FileExtensionValidator
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from pathlib import Path
import fitz  # PyMuPDF
import docx
import ollama  # Import Ollama for running LLaMA models
from collections import Counter
import re
import os
import uuid
import os.path
from django.conf import settings
import logging
import time
import traceback

# Setup specialized loggers
logger = logging.getLogger('resume_app')
security_logger = logging.getLogger('resume_app.security')
performance_logger = logging.getLogger('resume_app.performance')

# Access configuration from settings
SUPPORTED_EXTENSIONS = set(settings.RESUME_PROCESSOR['SUPPORTED_EXTENSIONS'])
MAX_FILE_SIZE = settings.RESUME_PROCESSOR['MAX_FILE_SIZE']
OLLAMA_MODEL = settings.RESUME_PROCESSOR['OLLAMA_MODEL']

# Django Form for file upload validation
class ResumeUploadForm(forms.Form):
    resume = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=[ext.lstrip('.') for ext in settings.RESUME_PROCESSOR['SUPPORTED_EXTENSIONS']])]
    )

    def clean_resume(self):
        file = self.cleaned_data['resume']
        if file.size > settings.RESUME_PROCESSOR['MAX_FILE_SIZE']:
            raise forms.ValidationError(f'File size must be under {settings.RESUME_PROCESSOR["MAX_FILE_SIZE"] // (1024 * 1024)}MB.')
        return file

# Resume Analyzer using Ollama
class ResumeAnalyzer:
    def __init__(self):
        self.model_name = settings.RESUME_PROCESSOR['OLLAMA_MODEL']
        logger.debug(f"Initialized ResumeAnalyzer with model: {self.model_name}")

    @staticmethod
    def extract_text_from_pdf(file_path: Path) -> str:
        """Extract text from PDF files."""
        start_time = time.time()
        logger.info(f"Starting PDF text extraction from: {file_path.name}")
        
        try:
            with fitz.open(file_path) as doc:
                text = " ".join(page.get_text() for page in doc)
                
            processing_time = time.time() - start_time
            performance_logger.info(f"PDF extraction completed in {processing_time:.2f}s for {file_path.name}")
            logger.debug(f"Extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            raise ValueError(f"Error processing PDF: {str(e)}")

    @staticmethod
    def extract_text_from_docx(file_path: Path) -> str:
        """Extract text from DOCX files."""
        start_time = time.time()
        logger.info(f"Starting DOCX text extraction from: {file_path.name}")
        
        try:
            doc = docx.Document(file_path)
            text = " ".join(para.text for para in doc.paragraphs)
            
            processing_time = time.time() - start_time
            performance_logger.info(f"DOCX extraction completed in {processing_time:.2f}s for {file_path.name}")
            logger.debug(f"Extracted {len(text)} characters from DOCX")
            return text
            
        except Exception as e:
            logger.error(f"DOCX extraction failed: {str(e)}")
            raise ValueError(f"Error processing DOCX: {str(e)}")

    def extract_resume_text(self, file_path: Path) -> str:
        """Determine file type and extract text accordingly."""
        logger.info(f"Extracting text from resume: {file_path.name}")
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        # Security: Ensure the file path is absolute and normalized
        file_path = file_path.resolve()
        
        # Security: Validate the file is within the media directory
        media_root = Path(settings.MEDIA_ROOT).resolve()
        if not str(file_path).startswith(str(media_root)):
            security_logger.warning(f"Security violation: Attempted to access file outside media directory: {file_path}")
            raise ValueError("Security error: Attempted to access file outside media directory")
        
        # Security: Re-validate file extension
        ext = file_path.suffix.lower()
        if ext not in settings.RESUME_PROCESSOR['SUPPORTED_EXTENSIONS']:
            security_logger.warning(f"Unsupported file format attempted: {ext}")
            raise ValueError(f"Unsupported file format: {ext}")
        
        # Security: Basic file type validation - check magic bytes for PDF files
        if ext == '.pdf':
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(5)
                    if header != b'%PDF-':
                        security_logger.warning(f"Invalid PDF signature for file: {file_path.name}")
                        raise ValueError("File is not a valid PDF")
            except Exception as e:
                logger.error(f"Error validating PDF: {str(e)}")
                raise ValueError(f"Error validating PDF: {str(e)}")
            
            logger.debug(f"PDF validation successful, proceeding with extraction")
            return self.extract_text_from_pdf(file_path)
        else:
            # For DOCX files, python-docx library will verify format
            logger.debug(f"Proceeding with DOCX extraction")
            return self.extract_text_from_docx(file_path)

    def get_word_frequency(self, text: str, num_words: int = 5) -> list:
        """Extract the most frequent meaningful words from text."""
        logger.debug(f"Calculating word frequency, text length: {len(text)} chars")
        start_time = time.time()
        
        # Common words to exclude
        stop_words = set(['the', 'and', 'a', 'to', 'in', 'of', 'for', 'on', 'with', 'at', 'from', 'by', 'about', 'as', 'i', 'my', 'me', 'is', 'are', 'was', 'were'])
        
        # Clean and tokenize text
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out stop words and short words
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Get word frequency
        word_freq = Counter(meaningful_words)
        
        # Log processing time
        processing_time = time.time() - start_time
        performance_logger.info(f"Word frequency calculation completed in {processing_time:.2f}s")
        
        # Return top N most common words with their frequencies
        result = word_freq.most_common(num_words)
        logger.debug(f"Found {len(result)} most common words")
        return result

    def generate_interview_questions(self, resume_text: str, num_questions: int = 10) -> list:
        """Generate interview questions using Ollama with LLaMA model."""
        logger.info(f"Generating {num_questions} interview questions using model: {self.model_name}")
        start_time = time.time()
        
        prompt = (
            "You are a highly skilled IT professional. Your task is to create specific and insightful interview questions based on the candidate's resume, "
            "These questions should effectively assess their experience and technical skills.\n\n"
            f"Below is an excerpt from the candidate's resume:\n{resume_text[:1500]}...\n\n"
            f"Please generate {num_questions} concise and well-structured interview questions:"
        )

        logger.debug(f"Sending prompt to LLM, length: {len(prompt)} chars")
        
        try:
            response = ollama.chat(model=self.model_name, messages=[{"role": "user", "content": prompt}])
            generated_text = response['message']['content']
            
            # Log LLM response time
            llm_time = time.time() - start_time
            performance_logger.info(f"LLM response received in {llm_time:.2f}s")
            
            logger.debug(f"Processing LLM response, length: {len(generated_text)} chars")
            
            # Extract questions from the generated text
            questions = []
            for line in generated_text.split('\n'):
                line = line.strip()
                if ('?' in line) or any(f"{i}." in line for i in range(1, num_questions + 1)):
                    questions.append(line.strip())

            # Clean up and ensure proper formatting
            questions = [q.split('.', 1)[-1].strip() if '.' in q else q for q in questions]
            questions = [q if q.endswith('?') else f"{q}?" for q in questions]

            # Ensure we have exactly num_questions
            while len(questions) < num_questions:
                questions.append(f"Question {len(questions) + 1}?")
                
            formatted_questions = [f"{i+1}. {q}" for i, q in enumerate(questions[:num_questions])]
            
            # Log full processing time
            total_time = time.time() - start_time
            performance_logger.info(f"Question generation completed in {total_time:.2f}s")
            logger.info(f"Successfully generated {len(formatted_questions)} questions")
            
            return formatted_questions

        except Exception as e:
            logger.error(f"Error in question generation: {str(e)}\n{traceback.format_exc()}")
            performance_logger.warning(f"Question generation failed after {time.time() - start_time:.2f}s")
            return [f"{i+1}. Default question {i+1}?" for i in range(num_questions)]

# Django View for Handling Resume Upload
def upload_resume(request):
    logger.info("=== Resume upload request received ===")
    request_start_time = time.time()
    
    # Get or create the resume analyzer instance
    if not hasattr(upload_resume, 'analyzer'):
        logger.debug("Creating new ResumeAnalyzer instance")
        upload_resume.analyzer = ResumeAnalyzer()
    
    # Initialize variables for cleanup
    fs = None
    saved_name = None
    file_path = None
    
    if request.method == "POST":
        logger.info("Processing POST request for resume upload")
        form = ResumeUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            logger.debug("Form validation successful")
            try:
                uploaded_file = request.FILES["resume"]
                logger.info(f"Resume file uploaded: {uploaded_file.name}, Size: {uploaded_file.size} bytes")
                
                # Check if file is empty
                if uploaded_file.size == 0:
                    logger.warning("Empty file uploaded")
                    return render(request, "upload.html", {
                        "form": form, 
                        "error": "The uploaded file is empty. Please upload a valid resume."
                    })
                
                # Security: Generate a secure random filename with original extension
                original_ext = os.path.splitext(uploaded_file.name)[1].lower()
                if original_ext not in settings.RESUME_PROCESSOR['SUPPORTED_EXTENSIONS']:
                    security_logger.warning(f"Unsupported file format uploaded: {original_ext}")
                    return render(request, "upload.html", {
                        "form": form, 
                        "error": f"Unsupported file format: {original_ext}. Please upload a PDF, DOC, or DOCX file."
                    })
                
                # Create a unique filename using UUID
                secure_filename = f"{uuid.uuid4().hex}{original_ext}"
                logger.debug(f"Generated secure filename: {secure_filename}")
                
                # Use FileSystemStorage to handle the upload
                fs = FileSystemStorage()
                
                # Save file with secure filename
                saved_name = fs.save(secure_filename, uploaded_file)
                file_path = Path(fs.path(saved_name))
                logger.info(f"File saved to: {file_path}")
                
                # Validate the path is within the media directory (prevent directory traversal)
                media_root = Path(fs.location).resolve()
                file_path = file_path.resolve()
                if not str(file_path).startswith(str(media_root)):
                    # If the resolved path is outside media directory, it's an attack attempt
                    security_logger.warning(f"Potential path traversal attack detected: {file_path}")
                    return render(request, "upload.html", {
                        "form": form, 
                        "error": "Security error: Invalid file path detected."
                    })

                # Extract text from resume
                text_extraction_start = time.time()
                try:
                    resume_text = upload_resume.analyzer.extract_resume_text(file_path)
                    
                    # Log text extraction performance
                    text_extraction_time = time.time() - text_extraction_start
                    performance_logger.info(f"Resume text extraction completed in {text_extraction_time:.2f}s")
                    
                    # Validate extracted text
                    if not resume_text or len(resume_text.strip()) < 50:
                        logger.warning(f"Insufficient text extracted from resume: {len(resume_text) if resume_text else 0} chars")
                        return render(request, "upload.html", {
                            "form": form, 
                            "error": "Could not extract sufficient text from the resume. Please ensure the document contains text and is not corrupted."
                        })
                        
                except ValueError as ve:
                    logger.error(f"Value error during text extraction: {str(ve)}")
                    return render(request, "upload.html", {
                        "form": form, 
                        "error": f"Error processing resume: {str(ve)}"
                    })
                except FileNotFoundError:
                    logger.error(f"File not found: {file_path}")
                    return render(request, "upload.html", {
                        "form": form, 
                        "error": "The uploaded file could not be processed. Please try again."
                    })
                except Exception as e:
                    logger.error(f"Unexpected error during text extraction: {str(e)}\n{traceback.format_exc()}")
                    return render(request, "upload.html", {
                        "form": form, 
                        "error": "An unexpected error occurred while processing your resume. Please try again or contact support."
                    })
                
                # Generate questions with timeout handling
                question_generation_start = time.time()
                try:
                    # Set a timeout for question generation
                    max_time = 30  # 30 seconds timeout
                    
                    interview_questions = upload_resume.analyzer.generate_interview_questions(resume_text, num_questions=10)
                    
                    # Check if generation took too long
                    question_generation_time = time.time() - question_generation_start
                    if question_generation_time > max_time:
                        performance_logger.warning(f"Question generation exceeded timeout: {question_generation_time:.2f}s > {max_time}s")
                    else:
                        performance_logger.info(f"Question generation completed in {question_generation_time:.2f}s")
                    
                    # Validate generated questions
                    if not interview_questions or len(interview_questions) < 3:
                        logger.error("Generated too few questions, using fallback questions")
                        interview_questions = [
                            "1. Could you elaborate on your professional experience?",
                            "2. What are your key technical skills?",
                            "3. Could you describe a challenging project you've worked on?",
                            "4. What are your career goals?",
                            "5. Why are you interested in this position?"
                        ]
                except Exception as e:
                    logger.error(f"Error during question generation: {str(e)}\n{traceback.format_exc()}")
                    # Fallback questions if Ollama fails
                    interview_questions = [
                        "1. Could you walk me through your resume?",
                        "2. What are your strongest technical skills?",
                        "3. Describe a challenging situation at work and how you handled it.",
                        "4. What are you looking for in your next role?",
                        "5. Do you have any questions about our company or the position?"
                    ]
                
                # Generate word frequency
                word_freq_start = time.time()
                try:
                    word_frequency = upload_resume.analyzer.get_word_frequency(resume_text)
                    performance_logger.info(f"Word frequency calculation completed in {time.time() - word_freq_start:.2f}s")
                except Exception as e:
                    logger.error(f"Error during word frequency calculation: {str(e)}")
                    word_frequency = [("error", 0)]
                
                # Log total request processing time
                total_processing_time = time.time() - request_start_time
                performance_logger.info(f"Total resume processing completed in {total_processing_time:.2f}s")
                logger.info("=== Resume processing completed successfully ===")
                
                return render(request, "questions.html", {
                    "resume_text": resume_text,
                    "interview_questions": interview_questions,
                    "word_frequency": word_frequency
                })
                
            except Exception as e:
                logger.error(f"Unexpected error in upload_resume: {str(e)}\n{traceback.format_exc()}")
                return render(request, "upload.html", {
                    "form": form, 
                    "error": "An unexpected error occurred. Please try again later."
                })
            finally:
                # Always clean up the file when done or if an error occurs
                if fs and saved_name and file_path and file_path.exists():
                    try:
                        fs.delete(saved_name)
                        logger.debug(f"Temporary file cleaned up: {saved_name}")
                    except Exception as e:
                        logger.error(f"Error deleting file {saved_name}: {str(e)}")
        
        # Handle invalid form
        else:
            logger.warning("Form validation failed")
            logger.debug(f"Form errors: {form.errors}")
            return render(request, "upload.html", {
                "form": form, 
                "error": "Invalid form submission. Please check the file type and size."
            })
    
    # Initial GET request
    else:
        logger.info("GET request received, rendering upload form")
        
    return render(request, "upload.html", {"form": ResumeUploadForm()})
