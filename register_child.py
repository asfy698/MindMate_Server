import cv2
import face_recognition
import pickle

cap = cv2.VideoCapture(0)

print("Press S to save child face")

while True:

    ret, frame = cap.read()

    cv2.imshow("Register Child", frame)

    key = cv2.waitKey(1)

    if key == ord("s"):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        encodings = face_recognition.face_encodings(
            rgb
        )

        if len(encodings) == 0:

            print("No face detected")
            continue

        with open(
            "child_face.pkl",
            "wb"
        ) as f:

            pickle.dump(
                encodings[0],
                f
            )

        print("Child saved")

        break

cap.release()
cv2.destroyAllWindows()